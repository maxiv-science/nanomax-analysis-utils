"""Unit tests for nmutils.core.Scan and dummyScan. No HDF5 files required."""

import numpy as np
import pytest

from nmutils.core.Scan import Scan
from nmutils.core.dummy import dummyScan


# Helpers
def make_scan(dataSource="fake-xrd", stepsize=100, framesize=50):
    """Return a dummyScan with one dataset already loaded."""
    s = dummyScan()
    s.addData("mydata", dataSource=dataSource, stepsize=stepsize, framesize=framesize)
    return s


# Initial state
class TestScanInitialState:
    def test_no_data(self):
        s = dummyScan()
        assert s.nDatasets == 0

    def test_positions_none(self):
        s = dummyScan()
        assert s.positions is None

    def test_nPositions_none(self):
        s = dummyScan()
        assert s.nPositions is None

    def test_nDimensions_none(self):
        s = dummyScan()
        assert s.nDimensions is None

    def test_empty_data_dict(self):
        s = dummyScan()
        assert s.data == {}


# addData
class TestAddData:
    def test_adds_dataset(self):
        s = dummyScan()
        s.addData("xrd", dataSource="fake-xrd", stepsize=100)
        assert "xrd" in s.data

    def test_positions_populated(self):
        s = make_scan()
        assert s.positions is not None
        assert s.positions.ndim == 2
        assert s.positions.shape[1] == 2  # 2-D scan

    def test_nDatasets_increments(self):
        s = dummyScan()
        s.addData("a", dataSource="fake-xrd", stepsize=100)
        s.addData("b", dataSource="fake-xrf", stepsize=100)
        assert s.nDatasets == 2

    def test_xrd_data_shape(self):
        s = make_scan(dataSource="fake-xrd", stepsize=100, framesize=50)
        data = s.data["mydata"]
        assert data.ndim == 3  # (positions, height, width)
        assert data.shape[0] == s.nPositions
        assert data.shape[1] == data.shape[2] == 50

    def test_xrf_data_shape(self):
        s = make_scan(dataSource="fake-xrf", stepsize=100, framesize=50)
        data = s.data["mydata"]
        assert data.ndim == 2  # (positions, spectrum_length)
        assert data.shape[0] == s.nPositions

    def test_scalar_data_shape(self):
        s = make_scan(dataSource="fake-scalar", stepsize=100, framesize=50)
        data = s.data["mydata"]
        assert data.ndim == 1  # one scalar per position
        assert data.shape[0] == s.nPositions

    def test_auto_name(self):
        s = dummyScan()
        s.addData(dataSource="fake-xrd", stepsize=100)
        assert "data0" in s.data

    def test_duplicate_name_raises(self):
        s = make_scan()
        with pytest.raises(ValueError, match="already exists"):
            s.addData("mydata", dataSource="fake-xrf", stepsize=100)

    def test_dataTitles_set(self):
        s = make_scan(dataSource="fake-xrd")
        assert isinstance(s.dataTitles["mydata"], str)

    def test_dataDimLabels_set(self):
        s = make_scan(dataSource="fake-xrd")
        labels = s.dataDimLabels["mydata"]
        # 2-D data (height, width) → 2 labels
        assert len(labels) == 2

    def test_dataAxes_set(self):
        s = make_scan(dataSource="fake-xrd")
        axes = s.dataAxes["mydata"]
        data = s.data["mydata"]
        assert len(axes) == data.ndim - 1


# removeData / listData
class TestRemoveAndList:
    def test_removeData_removes(self):
        s = make_scan()
        s.removeData("mydata")
        assert "mydata" not in s.data

    def test_removeData_missing_raises(self):
        s = make_scan()
        with pytest.raises(ValueError):
            s.removeData("nonexistent")

    def test_listData(self):
        s = dummyScan()
        s.addData("alpha", dataSource="fake-xrd", stepsize=100)
        s.addData("beta", dataSource="fake-xrf", stepsize=100)
        assert sorted(s.listData()) == ["alpha", "beta"]


# meanData
class TestMeanData:
    def test_meanData_shape(self):
        s = make_scan(dataSource="fake-xrd")
        mean = s.meanData("mydata")
        assert mean.shape == s.data["mydata"].shape[1:]

    def test_meanData_single_implicit(self):
        s = make_scan()
        mean = s.meanData()
        assert mean.shape == s.data["mydata"].shape[1:]

    def test_meanData_ambiguous_raises(self):
        s = dummyScan()
        s.addData("a", dataSource="fake-xrd", stepsize=100)
        s.addData("b", dataSource="fake-xrf", stepsize=100)
        with pytest.raises(ValueError, match="more than one"):
            s.meanData()


# copy
class TestCopy:
    def test_copy_full(self):
        s = make_scan()
        c = s.copy()
        np.testing.assert_array_equal(c.positions, s.positions)
        np.testing.assert_array_equal(c.data["mydata"], s.data["mydata"])

    def test_copy_is_independent(self):
        s = make_scan()
        c = s.copy()
        c.data["mydata"][0] = 0
        assert not np.array_equal(c.data["mydata"], s.data["mydata"])

    def test_copy_no_data(self):
        s = make_scan()
        c = s.copy(data=False)
        assert c.positions is None
        assert c.data["mydata"] is None

    def test_copy_no_data_preserves_metadata(self):
        s = make_scan()
        c = s.copy(data=False)
        assert "mydata" in c.dataTitles


# merge
class TestMerge:
    def test_merge_increases_positions(self):
        s1 = make_scan()
        s2 = make_scan()
        n_before = s1.nPositions
        s1.merge(s2)
        assert s1.nPositions == 2 * n_before

    def test_merge_increases_data(self):
        s1 = make_scan()
        s2 = make_scan()
        n_before = s1.data["mydata"].shape[0]
        s1.merge(s2)
        assert s1.data["mydata"].shape[0] == 2 * n_before

    def test_merge_incompatible_datasets_raises(self):
        s1 = make_scan()
        s2 = dummyScan()
        s2.addData("other", dataSource="fake-xrf", stepsize=100)
        with pytest.raises(AssertionError):
            s1.merge(s2)


# subset
class TestSubset:
    def test_subset_reduces_positions(self):
        s = make_scan(stepsize=100)
        xmin, xmax = np.min(s.positions[:, 0]), np.max(s.positions[:, 0])
        midx = (xmin + xmax) / 2
        posRange = np.array([[xmin, np.min(s.positions[:, 1])],
                              [midx, np.max(s.positions[:, 1])]])
        sub = s.subset(posRange)
        assert sub.nPositions < s.nPositions
        assert sub.nPositions > 0

    def test_subset_positions_in_range(self):
        s = make_scan(stepsize=100)
        posRange = np.array([[s.positions[:, 0].min(), s.positions[:, 1].min()],
                              [s.positions[:, 0].max(), s.positions[:, 1].max()]])
        sub = s.subset(posRange)
        assert sub.nPositions == s.nPositions

    def test_subset_closest(self):
        s = make_scan(stepsize=100)
        # a tiny range guaranteed to catch nothing
        center = np.mean(s.positions, axis=0)
        posRange = np.array([[center[0] - 0.001, center[1] - 0.001],
                              [center[0] + 0.001, center[1] + 0.001]])
        sub = s.subset(posRange, closest=True)
        assert sub.nPositions == 1


# interpolatedMap
class TestInterpolatedMap:
    def test_returns_three_arrays(self):
        s = make_scan()
        values = np.ones(s.nPositions)
        result = s.interpolatedMap(values, oversampling=1)
        assert len(result) == 3

    def test_all_same_shape(self):
        s = make_scan()
        values = np.ones(s.nPositions)
        x, y, z = s.interpolatedMap(values, oversampling=1)
        assert x.shape == y.shape == z.shape

    def test_origin_lr(self):
        s = make_scan()
        values = np.random.rand(s.nPositions)
        x, y, z = s.interpolatedMap(values, oversampling=1, origin="lr")
        assert z.shape == x.shape

    @pytest.mark.parametrize("origin", ["lr", "ll", "ur", "ul"])
    def test_origins(self, origin):
        s = make_scan()
        values = np.ones(s.nPositions)
        x, y, z = s.interpolatedMap(values, oversampling=1, origin=origin)
        assert x.shape == z.shape


# _updateOpts
class TestUpdateOpts:
    def _base_opts(self):
        return {
            "mode": {"value": "a", "type": ["a", "b", "c"], "doc": ""},
            "count": {"value": 1, "type": int, "doc": ""},
        }

    def test_valid_choice(self):
        s = dummyScan()
        opts = self._base_opts()
        result = s._updateOpts(opts, mode="b")
        assert result["mode"]["value"] == "b"

    def test_valid_type(self):
        s = dummyScan()
        opts = self._base_opts()
        result = s._updateOpts(opts, count=5)
        assert result["count"]["value"] == 5

    def test_unknown_key_raises(self):
        s = dummyScan()
        opts = self._base_opts()
        with pytest.raises(Exception, match="Unknown option"):
            s._updateOpts(opts, nonexistent=42)

    def test_wrong_type_raises(self):
        s = dummyScan()
        opts = self._base_opts()
        with pytest.raises(Exception, match="Data type"):
            s._updateOpts(opts, count="not_an_int")

    def test_bad_choice_raises(self):
        s = dummyScan()
        opts = self._base_opts()
        with pytest.raises(Exception, match="isn't on the menu"):
            s._updateOpts(opts, mode="z")

    def test_shallow_copy_inner_dicts_shared(self):
        """_updateOpts shallow-copies the outer dict; inner dicts are shared and mutated in-place."""
        s = dummyScan()
        opts = self._base_opts()
        result = s._updateOpts(opts, mode="b")
        # The returned dict reflects the update
        assert result["mode"]["value"] == "b"
        # The inner dict is shared, so the original is also modified
        assert opts["mode"]["value"] == "b"


# Scan abstract interface
class TestScanAbstractInterface:
    def test_readPositions_not_implemented(self):
        s = Scan()
        with pytest.raises(NotImplementedError):
            s._readPositions()

    def test_readData_not_implemented(self):
        s = Scan()
        with pytest.raises(NotImplementedError):
            s._readData("name")
