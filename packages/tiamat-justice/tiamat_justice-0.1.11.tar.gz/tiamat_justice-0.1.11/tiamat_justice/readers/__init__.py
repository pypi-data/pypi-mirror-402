def register_all_readers():
    from tiamat.readers import register_reader

    from .hdf5.bda import HDF5Reader as BDAHdf5Reader

    register_reader(BDAHdf5Reader)

    from .hdf5.fa import FaDeformationFieldReader, FaHdf5Reader

    register_reader(FaHdf5Reader)
    register_reader(FaDeformationFieldReader)

    from .bigtiff import BigTiffReader

    register_reader(BigTiffReader)

    from .deformation import HidraDeformationFieldReader, PyregDeformationFieldReader

    register_reader(HidraDeformationFieldReader)
    register_reader(PyregDeformationFieldReader)

    from .zarr.bda import ZarrReader as BDAZarrReader

    register_reader(BDAZarrReader)
