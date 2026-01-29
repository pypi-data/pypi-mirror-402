import requests
import pandas as pd
import urllib.parse
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path
import time

pd.set_option("display.max_columns", None)
pd.set_option("display.max_colwidth", None)
pd.set_option("display.expand_frame_repr", False)

# --- Feature and Observation classes ---
class Feature:
    def __init__(self, feature_json):
        self.id = feature_json["id"]
        self.name = feature_json["name"]
        self.coordinates = feature_json["shape"]["coordinates"]
        self.parameters = {param["name"]: param["value"] for param in feature_json["parameter"]}
        self.related_party = feature_json.get("relatedParty", [])
        self.contact_name = self.related_party[0].get("individualName", "") if self.related_party else ""
        self.contact_email = self.related_party[0].get("electronicMailAddress", "") if self.related_party else ""

    def to_dict(self):
        return {
            "ID": self.id,
            "Name": self.name,
            "Coordinates": f"{self.coordinates[0]}, {self.coordinates[1]}",
            "Source": self.parameters.get("source", ""),
            "Identifier": self.parameters.get("identifier", ""),
            "Contact Name": self.contact_name,
            "Contact Email": self.contact_email
        }

    def __repr__(self):
        return f"<Feature id={self.id} name={self.name}>"

class Observation:
    def __init__(self, obs_json):
        params = {param["name"]: param["value"] for param in obs_json.get("parameter", [])}
        self.id = obs_json["id"]
        self.source = params.get("source")
        self.observed_property = obs_json.get("observedProperty", {}).get("title")
        self.phenomenon_time_begin = obs_json.get("phenomenonTime", {}).get("begin")
        self.phenomenon_time_end = obs_json.get("phenomenonTime", {}).get("end")
        self.points = obs_json.get("result", {}).get("points", [])

    def to_dict(self):
        return {
            "ID": self.id,
            "Source": self.source,
            "Observed Property": self.observed_property,
            "Phenomenon Time Begin": self.phenomenon_time_begin,
            "Phenomenon Time End": self.phenomenon_time_end
        }

    def __repr__(self):
        return f"<Observation id={self.id} property={self.observed_property}>"

class Download:
    """Represents a single download record."""
    def __init__(self, download_json, client=None):
        self.client = client
        self.downloadName = download_json.get("downloadName")
        self.sizeInMB = download_json.get("sizeInMB")
        self.status = download_json.get("status")
        self.timestamp = download_json.get("timestamp")
        self.locator = download_json.get("locator")
        self.id = download_json.get("id")

    def to_dict(self):
        return {
            "File Name": self.downloadName,
            "ID": self.id,
            "Status": self.status,
            "Download Link": self.locator,
            "Size (in MB)": self.sizeInMB,
            "Timestamp": self.timestamp
        }

    def delete(self):
        if not self.client:
            raise RuntimeError("Download is not attached to a client.")
        return self.client.delete_download(self.id)

    def __repr__(self):
        return f"<Download id={self.id} name={self.downloadName} status={self.status}>"

class DeleteResult:
    def __init__(self, download_id: str, status: str = "deleted"):
        self.status = status
        self.id = download_id

    def to_dict(self):
        return {
            "status": self.status,
            "id": self.id
        }

    def __repr__(self):
        return f"ID = {self.id} | status = {self.status}"

# --- Collections with per-page support ---
class FeaturesCollection:
    """Collection of features with per-page pagination."""
    def __init__(self, client, constraints, initial_features=None, resumption_token=None, page=1, verbose=True):
        self.client = client
        self.constraints = constraints
        self.features = initial_features or []
        self.current_page_features = initial_features or []
        self.resumption_token = resumption_token
        self.completed = False
        self.page = page
        self.verbose = verbose
        if self.verbose:
            self._print_summary(len(self.current_page_features))

    def __len__(self):
        return len(self.features)

    def __getitem__(self, idx):
        return self.features[idx]

    def next(self):
        if self.completed or not self.resumption_token:
            print("No more data to fetch.")
            return self

        url = f"{self.client.base_url}features?{self.constraints.to_query()}&resumptionToken={urllib.parse.quote(self.resumption_token)}"
        self.page += 1
        if self.verbose:
            print(f"Retrieving page {self.page}: {url.replace(self.client.token, '***')}")
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()

        new_features = [Feature(f) for f in data.get("results", [])]
        self.current_page_features = new_features
        self.features.extend(new_features)
        token = data.get("resumptionToken")
        self.resumption_token = token.split(",")[0] if token else None
        self.completed = data.get("completed", True) or not self.resumption_token

        if self.verbose:
            self._print_summary(len(new_features))

        return self

    def to_df(self):
        return pd.DataFrame([f.to_dict() for f in self.current_page_features])

    def _print_summary(self, n_returned):
        prefix = "first" if self.page == 1 else "next"
        msg = f"Returned {prefix} {n_returned} features"
        if self.completed:
            print(msg + " (completed, data finished).")
        elif self.resumption_token:
            print(msg + " (not completed, more data available).\nUse .next() to move to the next page.")
        else:
            print(msg + " (completed, data finished).")  # edge case: no token but completed=False

class ObservationsCollection:
    """Collection of observations with per-page pagination."""
    def __init__(self, client, constraints, initial_obs=None, resumption_token=None, page=1, verbose=True):
        self.client = client
        self.constraints = constraints
        self.observations = initial_obs or []
        self.current_page_obs = initial_obs or []
        self.resumption_token = resumption_token
        self.completed = False
        self.page = page
        self.verbose = verbose
        if self.verbose:
            self._print_summary(len(self.current_page_obs))

    def __len__(self):
        return len(self.observations)

    def __getitem__(self, idx):
        return self.observations[idx]

    def next(self):
        if self.completed or not self.resumption_token:
            print("No more data to fetch.")
            return self

        url = f"{self.client.base_url}observations?{self.constraints.to_query()}&resumptionToken={urllib.parse.quote(self.resumption_token)}"
        self.page += 1
        if self.verbose:
            print(f"Retrieving page {self.page}: {url.replace(self.client.token, '***')}")
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()

        new_obs = [Observation(o) for o in data.get("member", [])]
        self.current_page_obs = new_obs
        self.observations.extend(new_obs)
        token = data.get("resumptionToken")
        self.resumption_token = token.split(",")[0] if token else None
        self.completed = data.get("completed", True) or not self.resumption_token

        if self.verbose:
            self._print_summary(len(new_obs))

        return self

    def to_df(self):
        return pd.DataFrame([o.to_dict() for o in self.current_page_obs])

    def _print_summary(self, n_returned):
        prefix = "first" if self.page == 1 else "next"
        msg = f"Returned {prefix} {n_returned} observations"
        if self.completed:
            print(msg + " (completed, data finished).")
        elif self.resumption_token:
            print(msg + " (not completed, more data available).\nUse .next() to move to the next page.")
        else:
            print(msg + " (completed, data finished).")  # edge case


class DownloadsCollection:
    """Collection of Download objects with simple list behavior."""

    def __init__(self, downloads_list=None):
        self.downloads = downloads_list or []

    def __len__(self):
        return len(self.downloads)

    def __getitem__(self, idx):
        return self.downloads[idx]

    def to_df(self):
        return pd.DataFrame([d.to_dict() for d in self.downloads])

    def __repr__(self):
        return f"<DownloadsCollection count={len(self.downloads)}>"

# --- Main DAB Client Class ---
class DABClient:
    """Generic DAB client for retrieving features and observations."""
    def __init__(self, token="{token}", view="{view}", base_url_template=None):
        self.token = token
        self.view = view
        # Use provided template or default generic template
        if base_url_template:
            self.base_url_template = base_url_template
        else:
            # Default generic template
            self.base_url_template = "https://gs-service-preproduction.geodab.eu/gs-service/services/essi/token/{token}/view/{view}/om-api/"

        # Format the URL if token/view are actual values
        if "{token}" not in self.token and "{view}" not in self.view:
            self.base_url = self.base_url_template.format(token=self.token, view=self.view)
        else:
            # Keep placeholders if token/view are default
            self.base_url = self.base_url_template

    def _obfuscate_download_id_in_url(self, url: str) -> str:
        """
        Obfuscate email part of download_id inside query string.
        Example:
        id=email@domain:uuid → id=***:uuid
        """
        if "id=" not in url:
            return url

        prefix, id_part = url.split("id=", 1)

        # Handle URL-encoded colon
        if "%3A" in id_part:
            _, uuid_part = id_part.split("%3A", 1)
            return f"{prefix}id=***%3A{uuid_part}"

        # Handle plain colon
        if ":" in id_part:
            _, uuid_part = id_part.split(":", 1)
            return f"{prefix}id=***:{uuid_part}"

        return url

    def _obfuscate_token(self, url: str) -> str:
        """Obfuscate token and download ID for safe printing."""
        url = url.replace(self.token, "***")
        url = self._obfuscate_download_id_in_url(url)
        return url

    def get_features(self, constraints, verbose=True):
        url = f"{self.base_url}features?{constraints.to_query()}"
        if verbose:
            print(f"Retrieving page 1: {self._obfuscate_token(url)}")
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()

        features_list = [Feature(f) for f in data.get("results", [])]
        token = data.get("resumptionToken")
        resumption_token = token.split(",")[0] if token else None
        collection = FeaturesCollection(self, constraints, features_list, resumption_token, page=1, verbose=verbose)
        collection.completed = data.get("completed", True)
        return collection

    def get_observations(self, constraints, verbose=True):
        url = f"{self.base_url}observations?{constraints.to_query()}"
        if verbose:
            print(f"Retrieving page 1: {self._obfuscate_token(url)}")
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()

        obs_list = [Observation(o) for o in data.get("member", [])]
        token = data.get("resumptionToken")
        resumption_token = token.split(",")[0] if token else None
        collection = ObservationsCollection(self, constraints, obs_list, resumption_token, page=1, verbose=verbose)
        collection.completed = data.get("completed", True)
        return collection

    def get_observation_with_data(self, observation_id, begin=None, end=None):
        url = self.base_url + f"observations?includeData=true&observationIdentifier={urllib.parse.quote(observation_id)}"
        if begin:
            url += "&beginPosition=" + urllib.parse.quote(begin)
        if end:
            url += "&endPosition=" + urllib.parse.quote(end)
        print("Retrieving " + self._obfuscate_token(url))
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
        if "member" not in data or not data["member"]:
            print("No observation data available for the requested time range.")
            return None
        return Observation(data["member"][0])

    # Generic helpers
    def features_to_df(self, features):
        if not features:
            return pd.DataFrame()
        return pd.DataFrame([f.to_dict() for f in features])

    def observations_to_df(self, observations):
        if not observations:
            return pd.DataFrame()
        return pd.DataFrame([o.to_dict() for o in observations])

    def points_to_df(self, observation):
        if not observation or not observation.points:
            return pd.DataFrame(columns=["Time", "Value"])
        return pd.DataFrame(
            [{"Time": p.get("time", {}).get("instant"), "Value": p.get("value")} for p in observation.points])

    def plot_observation(self, obs, title=None):
        if not obs or not obs.points:
            print("No data points available for this observation.")
            return
        times = [datetime.fromisoformat(p["time"]["instant"].replace("Z", "+00:00")) for p in obs.points]
        values = [p["value"] for p in obs.points]
        plt.figure(figsize=(10, 5))
        plt.plot(times, values, "o-", label=obs.observed_property)
        plt.title(title or f"{obs.observed_property} time series")
        plt.xlabel("Date")
        plt.ylabel(f"Value ({getattr(obs, 'uom', '')})")
        plt.grid(True)
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    # --- DOWNLOADS ---
    def create_download(self, download_constraints):
        """PUT: Submit a new download."""
        url = self.base_url + "downloads?" + download_constraints.to_query()

        # Print the URL (safe)
        print(f'DOWNLOAD URL: {self._obfuscate_token(url)}')

        # Make the PUT request
        resp = requests.put(url)
        resp.raise_for_status()

        # Create Download object from response
        download_obj = Download(resp.json(), client=self)

        # Now you can access id and status
        print(f'File "{download_obj.downloadName}" is {download_obj.status}.\nID = "{download_obj.id}"')

        return download_obj

    def get_download_status(self, download_id: str = None, verbose=True):
        """GET: Check status of a download (all or by ID)."""
        if download_id:
            url = self.base_url + f"downloads?id={urllib.parse.quote(download_id)}"
        else:
            url = self.base_url + "downloads"

        if verbose:
            print(f'STATUS URL: {self._obfuscate_token(url)}')  # always print by default

        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
        downloads_list = [Download(d, client=self) for d in data.get("results", [])]
        return DownloadsCollection(downloads_list)

    def delete_download(self, download_id: str):
        """DELETE a download by its ID."""
        if not download_id:
            raise ValueError("download_id is required")

        url = self.base_url + f"downloads?id={urllib.parse.quote(download_id)}"
        print(f'Deleting ID "{download_id}" ...\nDELETE URL: {self._obfuscate_token(url)}\"')

        resp = requests.delete(url)
        resp.raise_for_status()

        return DeleteResult(download_id)

    def _wait_for_download(self, download_id, poll_interval=3):
        print("Status: ", end="")
        previous_status = None

        def normalize(status):
            return status if status in ["Submitted", "Started", "Completed"] else "Downloading..."

        while True:
            obj = self.get_download_status(download_id, verbose=False)[0]
            current = normalize(obj.status)

            if current != previous_status:
                print(
                    current if previous_status is None
                    else f" ⟶ {current}",
                    end=""
                )
                previous_status = current

            if obj.status.lower() == "completed":
                print(f"\nDownload link: {obj.locator}")
                return obj

            time.sleep(poll_interval)

    def _save_locator(self, locator, filename=None, save_dir=None):
        save_dir = Path(save_dir) if save_dir else Path.home() / "Downloads"

        if not filename:
            # derive from URL
            filename = Path(urllib.parse.urlparse(locator).path).name

        save_path = save_dir / filename

        # --- Avoid overwriting existing file ---
        if save_path.exists():
            base, ext = save_path.stem, save_path.suffix
            i = 1
            while save_path.exists():
                save_path = save_dir / f"{base} ({i}){ext}"
                i += 1

        response = requests.get(locator, stream=True)
        response.raise_for_status()

        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        print(f"Download complete!\nFile saved to: {save_path}")
        return save_path

    def save_download(self, download_id, filename=None, save_dir=None):
        obj = self.get_download_status(download_id, verbose=False)[0]

        if obj.status.lower() != "completed":
            raise RuntimeError(
                f'Download "{download_id}" is not completed yet (status: {obj.status})'
            )

        return self._save_locator(
            obj.locator,
            filename=filename,
            save_dir=save_dir
        )

    def create_save_download(self, download_constraints, poll_interval=5,
                             filename=None, save_dir=None):
        download = self.create_download(download_constraints)
        completed = self._wait_for_download(download.id, poll_interval)

        return self.save_download(
            completed.id,
            filename=filename,
            save_dir=save_dir
        )

# Client subclasses
class WHOSClient(DABClient):
    def __init__(self, token, view="whos"):
        base_url_template = "https://whos.geodab.eu/gs-service/services/essi/token/{token}/view/{view}/om-api/"
        super().__init__(token, view, base_url_template)


class HISCentralClient(DABClient):
    def __init__(self, token, view="his-central"):
        base_url_template = "https://his-central.geodab.eu/gs-service/services/essi/token/{token}/view/{view}/om-api/"
        super().__init__(token, view, base_url_template)