from cdepy.cdejob import CdeSparkJob, CdeAirflowJob
from cdepy.cdeconnection import CdeConnection


def testCdeSparkJobDefinition():
    """
    Method to test if the creation of the createJobDefinition of a CdeSparkJob instance returns a dictionary
    """
    cdeConn = CdeConnection("testJobsApiUrl", "testUser", "testPassword")
    cdeSparkJob = CdeSparkJob(cdeConn)
    testCdeSparkJobDefinition = cdeSparkJob.createJobDefinition("testJob", "testResource", "testApp", SPARK_CONFS={"spark.pyspark.python": "python3"})
    assert isinstance(testCdeSparkJobDefinition, dict)

def testCdeAirflowJobDefinition():
    """
    Method to test if the creation of the createJobDefinition of a CdeAirflowJob instance returns a dictionary
    """
    cdeConn = CdeConnection("testJobsApiUrl", "testUser", "testPassword")
    cdeAirflowJob = CdeAirflowJob(cdeConn)
    testCdeAirflowJobDefinition = cdeAirflowJob.createJobDefinition("testJob", "testDagFile")
    assert isinstance(testCdeAirflowJobDefinition, dict)
