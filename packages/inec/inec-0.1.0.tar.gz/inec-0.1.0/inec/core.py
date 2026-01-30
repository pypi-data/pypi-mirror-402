from __future__ import annotations
import re
import os
import sys
import logging
import requests
import warnings
import collections
from requests.adapters import HTTPAdapter, Retry
from dataclasses import dataclass
import tempfile
from typing import Optional, NamedTuple

import certifi
from bs4 import BeautifulSoup
import pandas as pd


#HELPERS
#helper function for flat json responses
def _flatten(d, parent_key='', sep=''):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.abc.MutableMapping):
            items.extend(_flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

#helper for search a key in json responses
def _key_finder(data, target_key):
    if isinstance(data, dict):
        if target_key in data and isinstance(data[target_key], list):
            for item in data[target_key]:
                yield item

        for value in data.values():
            yield from _key_finder(value, target_key)

    elif isinstance(data, list):
        for item in data:
            yield from _key_finder(item, target_key)

TRUE_VALUES  = {"true", "1", "yes", "y", "t"}
FALSE_VALUES = {"false", "0", "no", "n", "f"}
#helper for dont trust the API!!
def to_bool(x):
    if pd.isna(x):
        return False
    if isinstance(x, bool):
        return x
    if isinstance(x, (int, float)):
        return bool(x)
    if isinstance(x, str):
        x = x.strip().lower()
        if x in TRUE_VALUES:
            return True
        if x in FALSE_VALUES:
            return False
    raise ValueError(f"Cannot parse boolean value: {x}")


#Classes
class INECError(Exception):
    """Base exception for INEC API errors."""
    pass

class INECAuthError(INECError):
    """Raised when authentication fails."""
    pass

class INECDataError(INECError):
    """Raised when data cannot be found or parsed."""
    pass

class INECDownloadError(INECError):
    """Raised when file downloading fails."""
    pass

class INECUserError(INECError):
    """Raised for specific user error cases."""

class INECInternalError(INECError):
    """Raised when internal not expected error occurs."""


@dataclass
class DB_details:
    href: str
    filename: str
    fileid: str

class DBDetailsUIResult(NamedTuple):
    items: list[DB_details]
    soup: BeautifulSoup
    url: str


class RepositoryManager:
    def __init__(self, parent: INECAPI):
        self.parent = parent

    def _extract_year(self, idno: str) -> Optional[int]:
            """Extracts a 4-digit year (19xx/20xx) from an idno string because start_year db column could not work as user expects"""
            years = re.findall(r'\b(19\d{2}|20\d{2})\b', idno)
            unique_years = list(set(years))
            
            if not unique_years:
                return None
            
            if len(unique_years) > 1:
                raise INECDataError(
                    f"Ambiguous date filter: Multiple years {unique_years} found in IDNO '{idno}'"
                )
            return int(unique_years[0])

    def show(self, repositoryid: str = None, full_table: bool = False) -> pd.DataFrame:
        url = self.parent.BASE_API_COLLEC_URL
        if repositoryid:
            url = f"{url}/{repositoryid}"
        
        self.parent.logger.info(f"Fetching repository data: {url}")
        resp = self.parent.sess.get(url).json()
        
        if not repositoryid:
            df = pd.DataFrame(resp.get('collections', {}))
        else:
            df = pd.DataFrame.from_records([resp])
            
        if df.empty: 
            self.parent.logger.info("No repositories found.")
            return df
            
        return df if full_table else df[['id', 'repositoryid', 'title', 'short_text']]

    def get(self, repositoryid: str, start_year: int, end_year: int) -> pd.DataFrame:
            """
            Retrieves and concatenates multiple datasets from a repository based on 
            years parsed from their IDNO.
            """

            if start_year is None or end_year is None:
                raise ValueError(
                    "Both 'start_year' and 'end_year' must be provided for batch retrieval."
                    "Example: api.repositories.get('REPO_ID', 2020, 2023)"
                )

            df_list = self.parent.datasets.show(repositoryid=repositoryid, full_table=True)
            if df_list.empty:
                self.parent.logger.warning(f"No datasets found for repository: {repositoryid}")
                return pd.DataFrame()

            valid_items = []
            for _, row in df_list.iterrows():
                try:
                    item_year = self._extract_year(row['idno'])
                    if not item_year:
                        continue
                    
                    if start_year and item_year < start_year:
                        continue
                    if end_year and item_year > end_year:
                        continue
                        
                    valid_items.append(row['idno'])
                except INECDataError as e:
                    self.parent.logger.error(f"Skipping row: {e}")
                    continue

            if not valid_items:
                self.parent.logger.info("No datasets matched the specified year filters.")
                return pd.DataFrame()

            self.parent.logger.info(f"Starting batch download for {len(valid_items)} items: {valid_items}")
            
            results = []
            for idno in valid_items:
                try:
                    df = self.parent.datasets.get(idno)
                    if df is not None:
                        # Inject metadata so user knows source after concatenation
                        from warnings import simplefilter 
                        simplefilter(action="ignore", category=pd.errors.PerformanceWarning) #this is not necessary due already have some comments in github pandas repo
                        df['_source_idno'] = idno
                        results.append(df)
                except Exception as e:
                    self.parent.logger.error(f"Failed to retrieve dataset {idno}: {e}")

            if not results:
                raise INECDownloadError("Batch process completed but no data was retrieved.")

            # --- IMPORTANT: Integrity Warning ---
            self.parent.logger.warning(
                "DATA INTEGRITY NOTICE: Performing blind concatenation of multiple datasets. "
                "This module does not validate schema consistency, column names, or data types "
                "across different years. Please verify that variables are harmonized before analysis."
                "'_source_idno' column is created by the module for track which file produce it"
            )

            self.parent.logger.info(f"Successfully concatenated {len(results)} datasets.")
            return pd.concat(results, ignore_index=True)


class DatasetsManager:
    def __init__(self, parent: INECAPI):
        self.parent = parent

    def _idno_to_id(self, idno: str) -> int:
        url = f"{self.parent.BASE_API_CATALOG_URL}/{idno}/export/ddi"
        try:
            resp = self.parent.sess.get(url).json()
            return int(resp.get('dataset', {}).get('id', []))
        except (ValueError, TypeError) as e:
            self.parent.logger.error(f"Failed to convert IDNO {idno} to ID: {e}")
            raise INECDataError(f"Could not resolve IDNO '{idno}' to an internal ID.") from e

    def _id_to_idno(self, id:int) -> str:
        url = f"{self.parent.BASE_CATALOG_URL}/{id}/study-description"
        html_file = self.parent.sess.get(url)
        soup = BeautifulSoup(html_file.text, 'html.parser')
        idno_container = soup.find('div', class_='field-study_desc.title_statement.idno')
        if idno_container:
            return idno_container.find('p').get_text(strip=True)

    def _autofill_form(self, soup: BeautifulSoup, url: str, id_val: int) -> list[DB_details]:
        bull_list_div = soup.find("div", class_="bull-list")
        tc_text = ""
        if bull_list_div:
            tc_text = bull_list_div.get_text(separator="\n", strip=True)
            self.parent.logger.info("--- TERMS AND CONDITIONS DETECTED ---")
            for line in tc_text.split('\n'):
                if line.strip():
                    self.parent.logger.info(f"T&C: {line.strip()}")
            self.parent.logger.info("---------------------------------------")
        else:
            self.parent.logger.warning("Access form detected but no T&C text found in 'bull-list'.")

        title_tag = soup.find('h1', id='dataset-title')
        survey_title = title_tag.get_text(strip=True) if title_tag else f"Dataset {id_val}"

        payload = {
            'ncsrf': self.parent.CCSRF_COOKIE_NAME,
            'surveytitle': survey_title,
            'surveyid': id_val,
            id_val: '',
            'abstract': self.parent.autofill_msg,
            'chk_agree': 'on',
            'submit': 'Enviar'
        }
        self.parent.logger.info(f"Submitting access form for: {survey_title}")
        self.parent.sess.post(url, data=payload, allow_redirects=True)
        return self._db_details_ui(id_val)

    def _db_details_ui(self, id_val: int) -> DBDetailsUIResult:
        _getmicrodataURL = f"{self.parent.BASE_CATALOG_URL}/{str(id_val)}/get-microdata"
        self.parent.logger.info(f"Accessing microdata URL: {_getmicrodataURL}")
        html_file = self.parent.sess.get(_getmicrodataURL)
        soup = BeautifulSoup(html_file.text, 'html.parser')

        links = soup.find_all('a', attrs={'data-file-id': True})
        
        found_items = [
                {'href': l.get('href'), 'filename': l.get('title'), 'fileid': l.get('data-file-id')}
                for l in links
            ]
        return found_items, soup, _getmicrodataURL

    def _db_details_api(self, dataset: int | str) -> list[DB_details]:
        resources = self.resources(dataset=dataset, full_table=True) #resources handle id/idno convertion
        resources["is_microdata"] = resources["is_microdata"].apply(to_bool)
        microdata = resources[resources["is_microdata"] == True]
        found_items = [
            {'href': r.get('_linksdownload'), 'filename': r.get('filename'), 'fileid': r.get('resource_id')}
            for _,r in microdata.iterrows()
        ]
        return found_items

    def _get_db_download_details(self, dataset: int | str) -> list[DB_details]:
        if isinstance(dataset, int):
            id_val = dataset
        elif isinstance(dataset, str):
            id_val = self._idno_to_id(idno=dataset)
        else:
            raise INECInternalError("Invalid format of variable <dataset>, valid types: (int for id | str for idno)")
        
        found_items, soup, _getmicrodataURL = self._db_details_ui(id_val=id_val)
        if not found_items and self.parent.autofill_msg:
            self.parent.logger.info("Form requirement detected. Attempting autofill...")
            found_items, _, _ = self._autofill_form(soup, _getmicrodataURL, id_val)
        if not found_items:
            self.parent.logger.info("Retrying using API instead of UI...")
            found_items = self._db_details_api(dataset=id_val) #retry using the API
        if not found_items:
            raise INECAuthError(f"Access restricted or not available. Please go to {_getmicrodataURL} and check that the DB exists.")
        return found_items

    def resources(self, dataset: int | str, full_table:bool = False):
        if isinstance(dataset, str):
            idno_val = dataset
        elif isinstance(dataset, int):
            idno_val = self._id_to_idno(id=dataset)
        else:
            raise INECDataError("Invalid format of variable <dataset>, valid types: (int for id | str for idno)")
        
        _getresourcesURL = f"{self.parent.BASE_DATASETS_API_URL}/{str(idno_val)}/resources"
        try:
            resp = self.parent.sess.get(_getresourcesURL).json()
            self.parent.logger.info(f"Accessing resources URL: {_getresourcesURL}")
            rows = resp.get('resources', {})
        except (ValueError, TypeError) as e:
            self.parent.logger.error(f"Failed to retrieve resources for {str(idno_val)}: {e}")
            raise INECDataError(f"Failed to retrieve resources of IDNO: '{str(idno_val)}'.") from e
        df_list=[]
        for i in rows:
            df = pd.DataFrame.from_dict(_flatten(i), orient='index').T
            df_list.append(df)
        df = pd.concat(df_list, sort=False).reset_index()
        if df.empty:
            self.parent.logger.info(f"No resources found for {str(idno_val)}.")
            return df
        return df if full_table else df[['resource_id', 'dctype', 'title', 'filename', 'dcformat', 'changed', 'dataset_idno','is_microdata']]
    
    def show(self, search: str = None, repositoryid: str = None, limit: int = 500, full_table: bool = False) -> pd.DataFrame:
        url = f"{self.parent.BASE_API_CATALOG_URL}"
        params = {
            "sort_by": "year_start", 
            "sort_order": "desc",
            "ps": limit
        }
        if search:
            params["sk"] = search
        if repositoryid:
            params["repo"] = repositoryid

        self.parent.logger.info(f"Querying catalog: {params}")
        resp = self.parent.sess.get(url, params=params).json()

        rows = resp.get('result', {}).get('rows', [])
        df = pd.DataFrame(rows)
        
        if df.empty:
            self.parent.logger.info("No datasets found matching criteria.")
            return df
            
        return df if full_table else df[['id', 'idno', 'repositoryid', 'form_model', 'title']]

    def get(self, dataset: list[dict] | int | str, fileid: int | str = None) -> pd.DataFrame:
        if not isinstance(dataset, list):
            items = self._get_db_download_details(dataset)
        else:
            items = dataset

        if len(items) > 1:
            if fileid is None:
                self.parent.logger.warning("Multiple files available. User must specify 'fileid'.")
                # Using print here as this is intended for user interaction/display, not just raising error
                print("\n--- Multiple files available. Please specify 'fileid' ---")
                print(pd.DataFrame(items)[['fileid', 'filename']])
                raise INECUserError(f"Multiple files available. Please specify 'fileid'")
            selected = next((i for i in items if str(i['fileid']) == str(fileid)), None)
            if not selected:
                raise INECDataError(f"File ID {fileid} not found in this dataset.")
        else:
            selected = items[0]
            self.parent.logger.info(f"Found DB data: {selected}")

        return self.parent._reader(selected)


class VariablesManager:
    def __init__(self, parent: INECAPI):
        self.parent = parent

    def show(self, dataset: int | str) -> pd.DataFrame:
        if isinstance(dataset, str):
            idno_val = dataset
        elif isinstance(dataset, int):
            idno_val = self.parent.datasets._id_to_idno(id=dataset)

        _getmicrodataURL = f"{self.parent.BASE_API_CATALOG_URL}/{str(idno_val)}/data-dictionary"
        self.parent.logger.info(f"Fetching variable dictionary: {_getmicrodataURL}")
        
        try:
            general_dict = self.parent.sess.get(_getmicrodataURL).json()
            result = _key_finder(general_dict, 'keywords')
            return pd.DataFrame(list(result))
        except Exception as e:
            self.parent.logger.error(f"Error fetching variables for {idno_val}: {e}")
            raise INECDataError(f"Could not fetch variables for {idno_val}") from e
        
    def dictionary(self, dataset: int | str) -> pd.DataFrame:
        if isinstance(dataset, int):
            id_val = dataset
        elif isinstance(dataset, str):
            id_val = self.parent.datasets._idno_to_id(idno=dataset)
        else:
            raise INECInternalError("Invalid format of variable <dataset>, valid types: (int for id | str for idno)")
        
        variables = []
        offset = 0
        limit = 300
        total_count = None
        while True:
            url = f"{self.parent.BASE_CATALOG_URL}/{id_val}/data-dictionary/F2?offset={offset}"
            response = self.parent.sess.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            if total_count is None:
                total_div = soup.find('div', class_='col-md-3', string=lambda t: "Total:" in t if t else False)
                if total_div:
                    total_text = "".join(filter(str.isdigit, total_div.get_text()))
                    total_count = int(total_text) if total_text else 0
                else:
                    # Fallback if UI changes or no variables exist
                    total_count = 1000

            var_rows = soup.find_all('div', class_='var-row')
            if not var_rows:
                break
            for row in var_rows:
                var_id_tag = row.find('a', class_='var-id')
                description_tag = row.find('div', class_='col')
                if var_id_tag:
                    variables.append({
                        'id': var_id_tag.get_text(strip=True),
                        'description': description_tag.get_text(strip=True) if description_tag else "",
                        'link': var_id_tag.get('href')
                    })
            offset += limit
            if offset >= total_count or not var_rows:
                break
        if not variables:
            raise INECInternalError(f"Unable to Parse variables, please visit: {url}")
        return pd.DataFrame(variables)


class INECAPI:
    def __init__(self, 
                api_key: str, 
                email: str, 
                password: str,
                autofill_msg: str = None,
                host: str = "sistemas.inec.cr/nada5.4/index.php",
                verbose: bool = True,
                verify_ssl: bool = False):
        
        self.verbose = verbose or "--verbose" in sys.argv
        self.logger = logging.getLogger("INECAPI")
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO if self.verbose else logging.WARNING)
        
        self.verify_ssl = verify_ssl
        self.verify = certifi.where() if verify_ssl else False

        retries = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[502, 503, 504], 
            allowed_methods=["GET", "POST"],
            respect_retry_after_header=False
        )
        self.BASE_URL = host if 'https://' in host else 'https://' + host
        self.BASE_API_URL = f"{self.BASE_URL}/api"
        self.BASE_API_CATALOG_URL = f"{self.BASE_API_URL}/catalog"
        self.BASE_API_COLLEC_URL = f"{self.BASE_API_CATALOG_URL}/collections"
        self.BASE_CATALOG_URL = f"{self.BASE_URL}/catalog"
        self.BASE_DATASETS_API_URL = f"{self.BASE_API_URL}/datasets"
        self.IHSN_COOKIE_NAME = "ihsn_nada"
        self.IHSN_COOKIE_VALUE = None
        self.CCSRF_COOKIE_NAME = "ccsrf"
        self.CCSRF_COOKIE_VALUE = None
        
        self.api_key = api_key
        self.email = email
        self.password = password
        self.autofill_msg = autofill_msg

        # Handle auth in another session
        self._auth_session = requests.Session()
        self._auth_session.verify = self.verify
        self._auth_session.mount("https://", HTTPAdapter(max_retries=retries))

        self.sess = requests.Session()
        self.sess.verify = self.verify
        self.sess.mount("https://", HTTPAdapter(max_retries=retries))
        self.sess.hooks['response'].append(self._hook_refresh_cookies_and_retry)
        self.sess.headers.update({
            "X-API-KEY": self.api_key,
            "User-Agent": "INEC-Python-Client/1.0",
            "Accept": "application/json"
        })

        if not verify_ssl:
            logging.captureWarnings(True)
            warn_logger = logging.getLogger("py.warnings")
            for handler in self.logger.handlers:
                warn_logger.addHandler(handler)
            warnings.formatwarning = lambda msg, category, filename, lineno, line=None: f"{category.__name__}: {msg}"
            warnings.warn("SSL verification is disabled. Insecure connections are being used.", UserWarning)
            
            from urllib3.exceptions import InsecureRequestWarning
            warnings.simplefilter("ignore", InsecureRequestWarning)

        self.logger.info("Authenticating...")
        self._authenticate()
        self.sess.cookies.update({
            self.IHSN_COOKIE_NAME: self.IHSN_COOKIE_VALUE
        })
        self.repositories = RepositoryManager(self)
        self.datasets = DatasetsManager(self)
        self.variables = VariablesManager(self)

    def _authenticate(self) -> bool:
        authURL = f"{self.BASE_URL}/auth/login"
        try:
            self._auth_session.get(authURL)
            self.CCSRF_COOKIE_VALUE = self._auth_session.cookies.get(self.CCSRF_COOKIE_NAME)
            self.sess.cookies.update({self.CCSRF_COOKIE_NAME: self.CCSRF_COOKIE_VALUE})
            
            payload = {
                "email": self.email, 
                "password": self.password, 
                "submit": "Iniciar+sesi%C3%B3n" 
            }
            response = self._auth_session.post(authURL, data=payload, allow_redirects=True)
            self.logger.debug(f'Auth Request response code: {response.status_code}')
            
            if int(response.status_code) == 200:
                self.IHSN_COOKIE_VALUE = response.cookies.get(self.IHSN_COOKIE_NAME)
                self.sess.cookies.update({self.IHSN_COOKIE_NAME: self.IHSN_COOKIE_VALUE})
                self.logger.info("Authentication successful.")
            else:
                raise INECAuthError(f"Authentication failed with response code: {response.status_code}")
        except requests.RequestException as e:
            raise INECAuthError(f"Network error during authentication: {e}")

    def _hook_refresh_cookies_and_retry(self, response, *args, **kwargs):
        if response.status_code == requests.codes.unauthorized:
            if response.request.headers.get('REATTEMPT'):
                self.logger.error('Cookies refresh failed, raising error')
                response.raise_for_status()

            self.logger.warning('Cookies expired (401 Error), refreshing Cookies...')

            # Refresh the Cookies
            self._authenticate()
            response.request.headers['REATTEMPT'] = '1'
            response.request.headers[self.IHSN_COOKIE_NAME] = self.IHSN_COOKIE_VALUE 

            self.logger.info('Retrying request with new Cookies')
            return self.sess.send(response.request)

        if int(response.status_code) == 500:
            raise INECError("Server response with 500 status code, possible ID not found or internal server error.")

        return response 

    def _reader(self, db_details: DB_details) -> pd.DataFrame:

        filename = db_details.get("filename", "unknown_file")
        url = db_details.get("href")

        if not url:
            raise INECDataError("No download URL found in database details.")

        self.logger.info(f"Downloading stream for {filename}...")

        ext = os.path.splitext(filename.lower())[1]
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp_path = tmp.name
            try:
                with self.sess.get(url, stream=True) as resp:
                    resp.raise_for_status()
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            tmp.write(chunk)
                tmp.flush()
                self.logger.info(f"Parsing {ext} file...")

                if ext == ".sav":
                    try:
                        return pd.read_spss(tmp_path)
                    except Exception:
                        self.logger.warning("Standard SPSS read failed. Retrying with pyreadstat/latin1.")
                        import pyreadstat
                        df, _ = pyreadstat.read_sav(tmp_path, encoding="latin1")
                        return df
                elif ext == ".csv":
                    return pd.read_csv(tmp_path)
                elif ext in [".xlsx", ".xls"]:
                    # Returns a dict of DataFrames if sheet_name=None
                    return pd.read_excel(tmp_path, sheet_name=None)
                elif ext == ".dta":
                    return pd.read_stata(tmp_path)
                elif ext == ".tsv":
                    return pd.read_csv(tmp_path, sep="\t")
                else:
                    raise INECDataError(f"Unsupported file format: {ext}")
            except Exception as e:
                raise INECDataError(f"Failed to process {filename}: {str(e)}")
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)