from unittest import TestLoader, TestSuite

from HtmlTestRunner import HTMLTestRunner
from testing.test_plumeFactory import Test_plumeFactory
from testing.test_plumeSensor import Test_plumeSensor
from testing.test_sensorCommunityFactroy import Test_sensorCommunityFactory
from testing.test_sensorCommunitySensor import Test_sensorCommunitySensor
from testing.test_SensorFactoryWrapper import Test_SensorFactoryWrapper
from testing.test_sensorReadable import Test_sensorReadable
from testing.test_sensorWriteable import Test_sensorWriteable
from testing.test_zephyrFactory import Test_zephyrFactory
from testing.test_zephyrSensor import Test_zephyrSensor

# load all tests from the test classes in any order
test_1 = TestLoader().loadTestsFromTestCase(Test_plumeFactory)
test_2 = TestLoader().loadTestsFromTestCase(Test_plumeSensor)
test_3 = TestLoader().loadTestsFromTestCase(Test_SensorFactoryWrapper)
test_4 = TestLoader().loadTestsFromTestCase(Test_sensorReadable)
test_5 = TestLoader().loadTestsFromTestCase(Test_sensorWriteable)
test_6 = TestLoader().loadTestsFromTestCase(Test_zephyrFactory)
test_7 = TestLoader().loadTestsFromTestCase(Test_zephyrSensor)
test_8 = TestLoader().loadTestsFromTestCase(Test_sensorCommunityFactory)
test_9 = TestLoader().loadTestsFromTestCase(Test_sensorCommunitySensor)

# run all tests in order (but test_7 is run first to issues with sensor ids)
suite = TestSuite([test_1, test_2, test_3, test_4, test_5, test_6, test_7, test_8, test_9])

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
