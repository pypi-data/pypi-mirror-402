def test_import():
    import ptcfextract
    assert hasattr(ptcfextract, "compute_lps_features")
    assert hasattr(ptcfextract, "process_pointcloud")
