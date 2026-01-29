from cdepy.cderesource import CdeFilesResource, CdePythonResource

def testCdeFilesResourceDefinition():
    """
    Method to test if the creation of the cdeFilesResourceDefinition of a CdeFilesResource instance returns a dictionary
    """
    testCdeFilesResource = CdeFilesResource("testFilesResource")
    testCdeSparkJobDefinition = testCdeFilesResource.createResourceDefinition()
    assert isinstance(testCdeSparkJobDefinition, dict)

def testCdePythonResourceDefinition():
    """
    Method to test if the creation of the cdePythonResourceDefinition of a CdePythonResource instance returns a dictionary
    """
    testCdePythonResource = CdePythonResource("testPythonResource")
    testCdePythonResourceDefinition = testCdePythonResource.createResourceDefinition()
    assert isinstance(testCdePythonResourceDefinition, dict)
