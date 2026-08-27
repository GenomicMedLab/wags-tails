# ruff: noqa: SLF001 ARG005
from dataclasses import dataclass

import pytest

from wags_tails.core.exceptions import ReleaseParsingError
from wags_tails.core.models import Asset, AssetBundle, Dataset, Source
from wags_tails.core.version import DotSeparatedVersionScheme, Version


def test_source_get_name():
    source = Source(id="ncbi", name="NCBI")

    assert source.get_name() == "NCBI"


def test_source_get_name_falls_back_to_id():
    source = Source(id="ncbi", name=None)

    assert source.get_name() == "ncbi"


@pytest.fixture
def source():
    return Source(id="test_source", name="Test Source")


@pytest.fixture
def asset_type(source):
    class TestAsset(Asset):
        _source = source
        _id = "things"
        _filetype = "txt"

    return TestAsset


@pytest.fixture
def asset_type_without_id(source):
    class TestAssetWithoutId(Asset):
        _source = source
        _filetype = "json"

    return TestAssetWithoutId


@pytest.fixture
def version():
    return Version.parse("v1.2", DotSeparatedVersionScheme)


def test_asset_get_filename(asset_type, version):
    assert asset_type.get_filename(version) == "test_source_things_v1.2.txt"


def test_asset_get_filename_without_id(asset_type_without_id, version):
    assert asset_type_without_id.get_filename(version) == "test_source_v1.2.json"


def test_asset_get_file_glob(asset_type):
    assert asset_type.get_file_glob() == "test_source_things_*.txt"


@pytest.fixture(autouse=True)
def reset_dataset_registry():
    original = {
        source_id: datasets.copy() for source_id, datasets in Dataset._registry.items()
    }

    Dataset._registry.clear()

    yield

    Dataset._registry.clear()
    Dataset._registry.update(original)


@pytest.mark.parametrize(
    "missing_attribute",
    [
        "source",
        "id",
        "name",
        "version_scheme",
        "_payload_type",
    ],
)
def test_dataset_requires_class_attributes(missing_attribute, source, asset_type):
    attributes = {
        "source": source,
        "id": "test_dataset",
        "name": "Test Dataset",
        "version_scheme": DotSeparatedVersionScheme,
        "_payload_type": asset_type,
        "_get_latest_version": lambda self, session: None,
        "_stage_release": lambda self, staging_dir, version, session: None,
    }
    del attributes[missing_attribute]

    with pytest.raises(TypeError, match=missing_attribute):
        type("TestDataset", (Dataset,), attributes)


def make_dataset_type(
    *,
    source,
    asset_type,
    dataset_id="test_dataset",
    name="Test Dataset",
    version_scheme=DotSeparatedVersionScheme,
    class_name="TestDataset",
):
    """Create a minimal concrete Dataset subclass for use in tests.

    Dataset subclasses must declare several class attributes and implement the
    abstract version lookup and release staging methods. This helper provides
    those requirements so tests can construct Dataset types while varying only
    the attributes relevant to the behavior under test.

    Creating the returned type invokes ``Dataset.__init_subclass__`` and
    therefore performs normal Dataset subclass validation and registration.

    :param source: Source associated with the test dataset.
    :param asset_type: Asset or AssetBundle type used as the dataset payload.
    :param dataset_id: Dataset identifier. May be ``None`` for a source with a
        single dataset.
    :param name: User-facing dataset name.
    :param version_scheme: Version scheme used by the dataset.
    :param class_name: Name assigned to the dynamically created class.
    :return: Concrete Dataset subclass configured with the supplied values.
    """
    return type(
        class_name,
        (Dataset,),
        {
            "source": source,
            "id": dataset_id,
            "name": name,
            "version_scheme": version_scheme,
            "_payload_type": asset_type,
            "_get_latest_version": lambda self, session: None,
            "_stage_release": lambda self, staging_dir, version, session: None,
        },
    )


def test_dataset_allows_single_dataset_without_id(source, asset_type):
    dataset_type = make_dataset_type(
        source=source,
        asset_type=asset_type,
        dataset_id=None,
    )

    assert Dataset._registry[source.id] == [dataset_type]


def test_dataset_requires_ids_when_source_has_multiple_datasets(source, asset_type):
    make_dataset_type(
        source=source,
        asset_type=asset_type,
        dataset_id=None,
    )

    with pytest.raises(TypeError, match="each dataset must define an id"):
        make_dataset_type(
            source=source,
            asset_type=asset_type,
            dataset_id="second",
        )


def test_dataset_requires_unique_ids_within_source(source, asset_type):
    make_dataset_type(
        source=source,
        asset_type=asset_type,
        dataset_id="same",
    )

    with pytest.raises(TypeError, match="must be unique"):
        make_dataset_type(
            source=source,
            asset_type=asset_type,
            dataset_id="same",
        )


def test_dataset_allows_same_id_for_different_sources(source, asset_type):
    other_source = Source(id="other_source", name="Other Source")

    first = make_dataset_type(
        source=source,
        asset_type=asset_type,
        dataset_id="same",
    )

    second = make_dataset_type(
        source=other_source,
        asset_type=asset_type,
        dataset_id="same",
    )

    assert Dataset._registry[source.id] == [first]
    assert Dataset._registry[other_source.id] == [second]


def test_dataset_qualified_id_without_dataset_id(source, asset_type):
    dataset_type = make_dataset_type(
        source=source,
        asset_type=asset_type,
        dataset_id=None,
    )

    assert dataset_type.qualified_id() == "test_source"


def test_dataset_qualified_id_with_dataset_id(source, asset_type):
    dataset_type = make_dataset_type(
        source=source,
        asset_type=asset_type,
        dataset_id="test_dataset",
    )

    assert dataset_type.qualified_id() == "test_source_test_dataset"


def test_dataset_dir_without_dataset_id(source, asset_type, tmp_path):
    dataset_type = make_dataset_type(
        source=source,
        asset_type=asset_type,
        dataset_id=None,
    )

    dataset = dataset_type()

    assert dataset.dataset_dir(tmp_path) == tmp_path / "test_source"


def test_dataset_dir_with_dataset_id(source, asset_type, tmp_path):
    dataset_type = make_dataset_type(
        source=source,
        asset_type=asset_type,
        dataset_id="test_dataset",
    )

    dataset = dataset_type()

    assert dataset.dataset_dir(tmp_path) == tmp_path / "test_source" / "test_dataset"


def test_parse_release_directory(source, asset_type, tmp_path):
    dataset_type = make_dataset_type(
        source=source,
        asset_type=asset_type,
        version_scheme=DotSeparatedVersionScheme,
    )
    dataset = dataset_type()

    release_directory = tmp_path / "v1.2.3"
    release_directory.mkdir()

    version = dataset.parse_release_directory(release_directory)

    assert version.raw == "v1.2.3"
    assert version.parsed == (1, 2, 3)
    assert version.scheme is DotSeparatedVersionScheme


def test_parse_release_directory_missing_directory(source, asset_type, tmp_path):
    dataset_type = make_dataset_type(
        source=source,
        asset_type=asset_type,
        version_scheme=DotSeparatedVersionScheme,
    )
    dataset = dataset_type()

    release_directory = tmp_path / "v1.2.3"

    with pytest.raises(ReleaseParsingError, match="release directory does not exist"):
        dataset.parse_release_directory(release_directory)


def test_parse_release_directory_invalid_version(source, asset_type, tmp_path):
    dataset_type = make_dataset_type(
        source=source,
        asset_type=asset_type,
        version_scheme=DotSeparatedVersionScheme,
    )
    dataset = dataset_type()

    release_directory = tmp_path / "not-a-version"
    release_directory.mkdir()

    with pytest.raises(
        ReleaseParsingError,
        match="Failed to parse release version",
    ):
        dataset.parse_release_directory(release_directory)


def test_load_release_with_single_asset(source, asset_type, tmp_path):
    dataset_type = make_dataset_type(
        source=source,
        asset_type=asset_type,
        version_scheme=DotSeparatedVersionScheme,
    )
    dataset = dataset_type()

    release_directory = tmp_path / "v1.2.3"
    release_directory.mkdir()

    version = Version.parse("v1.2.3", DotSeparatedVersionScheme)
    asset_path = release_directory / asset_type.get_filename(version)
    asset_path.write_text("contents")

    release = dataset.load_release(release_directory)

    assert release.dataset is dataset
    assert release.version == version
    assert isinstance(release.payload, asset_type)
    assert release.payload.location == asset_path


def test_load_release_with_asset_bundle(source, tmp_path):
    class FirstAsset(Asset):
        _source = source
        _id = "first"
        _filetype = "txt"

    class SecondAsset(Asset):
        _source = source
        _id = "second"
        _filetype = "json"

    @dataclass(frozen=True)
    class TestAssetBundle(AssetBundle):
        first: FirstAsset
        second: SecondAsset

    dataset_type = make_dataset_type(
        source=source,
        asset_type=TestAssetBundle,
        version_scheme=DotSeparatedVersionScheme,
    )
    dataset = dataset_type()

    release_directory = tmp_path / "v1.2.3"
    release_directory.mkdir()

    version = Version.parse("v1.2.3", DotSeparatedVersionScheme)

    first_path = release_directory / FirstAsset.get_filename(version)
    second_path = release_directory / SecondAsset.get_filename(version)

    first_path.write_text("first")
    second_path.write_text("second")

    release = dataset.load_release(release_directory)

    assert release.dataset is dataset
    assert release.version == version
    assert isinstance(release.payload, TestAssetBundle)
    assert release.payload.first.location == first_path
    assert release.payload.second.location == second_path


def test_load_release_missing_asset(source, asset_type, tmp_path):
    dataset_type = make_dataset_type(
        source=source,
        asset_type=asset_type,
        version_scheme=DotSeparatedVersionScheme,
    )
    dataset = dataset_type()

    release_directory = tmp_path / "v1.2.3"
    release_directory.mkdir()

    with pytest.raises(FileNotFoundError):
        dataset.load_release(release_directory)
