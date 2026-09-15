"""Provide storage for release assets"""

import logging
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from wags_tails.core.models import AssetsT, Dataset, Release
from wags_tails.core.operation import OperationConfig
from wags_tails.core.paths import resolve_data_dir

logger = logging.getLogger(__name__)


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
        logger.debug(
            "Initialized local store at %s (offline=%s)", self.data_dir, self._offline
        )

    def get_latest(
        self,
        dataset: type[Dataset[AssetsT]],
        *,
        offline: bool | None = None,
        force_refresh: bool = False,
    ) -> Release[AssetsT] | None:
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
        logger.debug(
            "Getting latest release for %s (offline=%s, force_refresh=%s)",
            dataset.qualified_id(),
            offline,
            force_refresh,
        )
        if offline and force_refresh:
            logger.warning(
                "Cannot force-refresh dataset %s while offline", dataset.qualified_id()
            )
            msg = "'offline' and 'force_refresh' cannot both be True."
            raise ValueError(msg)

        latest_local_release = self._find_latest_local_release(dataset)

        if offline:
            if latest_local_release is None:
                logger.info(
                    "No cached release found for offline dataset %s",
                    dataset.qualified_id(),
                )
            else:
                logger.info(
                    "Using cached release for offline dataset %s",
                    dataset.qualified_id(),
                )
            return latest_local_release

        if force_refresh:
            logger.info("Force-refreshing dataset %s", dataset.qualified_id())
            return self._stash_latest_release(dataset, overwrite_existing=force_refresh)

        latest_published_version = dataset.get_latest_version(self._session_config)
        if (
            latest_local_release is None
            or latest_local_release.version < latest_published_version
        ):
            logger.info(
                "Refreshing cached release for dataset %s", dataset.qualified_id()
            )
            return self._stash_latest_release(dataset, overwrite_existing=force_refresh)

        logger.info(
            "Using current cached release %s for dataset %s",
            latest_local_release.version,
            dataset.qualified_id(),
        )
        return latest_local_release

    def _find_latest_local_release(
        self, dataset: type[Dataset[AssetsT]]
    ) -> Release[AssetsT] | None:
        """Return the newest cached release of a dataset.

        :param dataset: Dataset to inspect.
        :return: The newest cached release, or ``None`` if none are available.
        """
        dataset_dir = dataset.dataset_dir(self.data_dir)

        if not dataset_dir.is_dir():
            logger.debug("No cache directory for dataset %s", dataset.qualified_id())
            return None

        releases: list[Release[AssetsT]] = []

        for child in dataset_dir.iterdir():
            if not child.is_dir():
                continue
            try:
                _ = dataset.version_scheme.parse(child.name)
            except ValueError:
                # Ignore directories that are not valid versions.
                logger.debug("Ignoring invalid release directory %s", child)
                continue
            releases.append(dataset.load_release(child))

        if not releases:
            logger.debug(
                "No valid cached releases found for dataset %s", dataset.qualified_id()
            )
            return None

        latest_release = max(releases, key=lambda r: r.version)
        logger.debug(
            "Found cached release %s for dataset %s",
            latest_release.version,
            dataset.qualified_id(),
        )
        return latest_release

    def _stash_latest_release(
        self, dataset: type[Dataset[AssetsT]], overwrite_existing: bool
    ) -> Release[AssetsT]:
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
                logger.warning(
                    "Release %s already exists for dataset %s",
                    version,
                    dataset.qualified_id(),
                )
                msg = f"Release {version} already exists"
                raise RuntimeError(msg)

            staging_dir = Path(tmp) / version.raw
            staging_dir.mkdir(exist_ok=True, parents=True)
            logger.debug(
                "Staging dataset %s release %s in %s",
                dataset.qualified_id(),
                version,
                staging_dir,
            )
            dataset.stage_release(staging_dir, version, self._session_config)

            staged_release = dataset.load_release(staging_dir)

            release_dir.mkdir(parents=True)

            for staged_file in staged_release.payload.get_files():
                shutil.move(staged_file, release_dir / staged_file.name)
        cached_release = dataset.load_release(release_dir)
        logger.info(
            "Cached dataset %s release %s at %s",
            dataset.qualified_id(),
            version,
            release_dir,
        )
        return cached_release
