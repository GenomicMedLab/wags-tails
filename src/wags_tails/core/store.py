"""Provide storage for release assets"""

import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from wags_tails.core.models import Dataset, Release
from wags_tails.core.operation import OperationConfig
from wags_tails.core.paths import resolve_data_dir


class LocalStore:
    """Filesystem-based dataset storage"""

    def __init__(
        self,
        data_dir: Path | None = None,
        *,
        offline: bool = False,
        show_progress: bool = True,
    ):
        """Initialize storage instance

        :param data_dir: Root directory for storing Wags Tails data. If omitted,
            resolve using the configured/default data directory.
        :param offline: Default offline policy for this store. Individual method
            calls may override this behavior.
        :param show_progress: whether to show a progress bar for download operations
        """
        self.data_dir = resolve_data_dir(data_dir)
        self._offline = offline
        self._session_config = OperationConfig(show_progress=show_progress)

    def get_latest(
        self,
        dataset: type[Dataset],
        *,
        offline: bool | None = None,
        force_refresh: bool = False,
    ) -> Release | None:
        """Return the newest available release of a dataset.

        By default, returns the latest published release, downloading it if the
        locally cached release is missing or outdated.

        :param dataset: Dataset to retrieve.
        :param offline: If ``True``, never contact the upstream source. If ``None``,
            defer to policy configured at class initialization. Return the
            newest locally cached release, or ``None`` if no local release exists.
        :param force_refresh: If ``True``, always download the latest published
            release from the source, even if the newest cached release is already
            current.
        :return: The requested release, or ``None`` if ``offline`` is enabled and
            no local release is available.
        """
        offline = self._offline if offline is None else offline
        if offline and force_refresh:
            msg = "'offline' and 'force_refresh' cannot both be True."
            raise ValueError(msg)

        latest_local_release = self._find_latest_local_release(dataset)

        if offline:
            return latest_local_release

        if force_refresh:
            return self._stash_latest_release(dataset, overwrite_existing=force_refresh)

        latest_published_version = dataset.get_latest_version(self._session_config)
        if (
            latest_local_release is None
            or latest_local_release.version < latest_published_version
        ):
            return self._stash_latest_release(dataset, overwrite_existing=force_refresh)

        return latest_local_release

    def _find_latest_local_release(self, dataset: type[Dataset]) -> Release | None:
        """Return the newest cached release of a dataset.

        :param dataset: Dataset to inspect.
        :return: The newest cached release, or ``None`` if none are available.
        """
        dataset_dir = dataset.dataset_dir(self.data_dir)

        if not dataset_dir.is_dir():
            return None

        releases: list[Release] = []

        for child in dataset_dir.iterdir():
            if not child.is_dir():
                continue
            try:
                _ = dataset.version_scheme.parse(child.name)
            except ValueError:
                # Ignore directories that are not valid versions.
                continue
            releases.append(dataset.load_release(child))

        if not releases:
            return None

        return max(releases, key=lambda r: r.version)

    def _stash_latest_release(
        self, dataset: type[Dataset], overwrite_existing: bool
    ) -> Release:
        """Download and cache the latest published release of a dataset.

        The dataset implementation is responsible for downloading and preparing the
        release within a temporary staging directory. Once staging completes
        successfully, the release is atomically installed into the local cache.

        :param dataset: Dataset whose latest release should be cached.
        :param overwrite_existing: whether to force overwrite if release already exists
            in storage
        :return: The cached release.
        """
        with TemporaryDirectory() as tmp:
            version = dataset.get_latest_version(self._session_config)
            release_dir = dataset.dataset_dir(self.data_dir) / version.raw
            if not overwrite_existing and release_dir.exists():
                msg = f"Release {version} already exists"
                raise RuntimeError(msg)

            staging_dir = Path(tmp) / version.raw
            staging_dir.mkdir(exist_ok=True, parents=True)
            dataset.stage_release(staging_dir, version, self._session_config)

            release_dir.parent.mkdir(exist_ok=True, parents=True)
            shutil.move(staging_dir, release_dir)

        return dataset.load_release(release_dir)
