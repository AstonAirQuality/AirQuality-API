from unittest import TestLoader, TestSuite

from HtmlTestRunner import HTMLTestRunner
from testing.test_plumeFactory import Test_plumeFactory
from testing.test_plumeSensor import Test_plumeSensor
from testing.test_purpleAirFactory import Test_purpleAirFactory
from testing.test_purpleAirSensor import Test_purpleAirSensor
from testing.test_sensorCommunityFactory import Test_sensorCommunityFactory
from testing.test_sensorCommunitySensor import Test_sensorCommunitySensor
from testing.test_SensorPlatformFactoryWrapper import Test_SensorFactoryWrapper
from testing.test_sensorReadable import Test_sensorReadable
from testing.test_sensorWriteable import Test_sensorWriteable
from testing.test_zephyrFactory import Test_zephyrFactory
from testing.test_zephyrSensor import Test_zephyrSensor

# load all tests from the test classes in any order
test_1 = TestLoader().loadTestsFromTestCase(Test_plumeFactory)
test_2 = TestLoader().loadTestsFromTestCase(Test_plumeSensor)
test_3 = TestLoader().loadTestsFromTestCase(Test_zephyrFactory)
test_4 = TestLoader().loadTestsFromTestCase(Test_zephyrSensor)
test_5 = TestLoader().loadTestsFromTestCase(Test_sensorCommunityFactory)
test_6 = TestLoader().loadTestsFromTestCase(Test_sensorCommunitySensor)
test_7 = TestLoader().loadTestsFromTestCase(Test_purpleAirFactory)
test_8 = TestLoader().loadTestsFromTestCase(Test_purpleAirSensor)
test_9 = TestLoader().loadTestsFromTestCase(Test_SensorFactoryWrapper)
test_10 = TestLoader().loadTestsFromTestCase(Test_sensorReadable)
test_11 = TestLoader().loadTestsFromTestCase(Test_sensorWriteable)

# run all tests in order
suite = TestSuite([test_1, test_2, test_3, test_4, test_5, test_6, test_7, test_8, test_9, test_10, test_11])

runner = HTMLTestRunner(
    output="testing/output",
    report_name="DataIngestionPipeline_test_report",
    combine_reports=True,
    add_timestamp=False,
    open_in_browser=False,
    report_title="Data Ingestion Pipeline Test Report",
    descriptions=True,
    verbosity=2,
)

runner.run(suite)
