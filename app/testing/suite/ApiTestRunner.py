from unittest import TestLoader, TestSuite

from HtmlTestRunner import HTMLTestRunner
from testing.test_api_route_auth import Test_Api_3_Auth
from testing.test_api_route_bgtasks import Test_Api_7_BackgroundTasks
from testing.test_api_route_logs import Test_Api_5_Logs
from testing.test_api_route_sensor import Test_Api_2_Sensor
from testing.test_api_route_sensorSummary import Test_Api_6_SensorSummary
from testing.test_api_route_sensorType import Test_Api_1_Sensor_Type
from testing.test_api_route_user import Test_Api_4_Users
from testing.test_main import Test_Api_Main

# load all tests from the test classes in order
test_1 = TestLoader().loadTestsFromTestCase(Test_Api_1_Sensor_Type)
test_2 = TestLoader().loadTestsFromTestCase(Test_Api_2_Sensor)
test_3 = TestLoader().loadTestsFromTestCase(Test_Api_3_Auth)
test_4 = TestLoader().loadTestsFromTestCase(Test_Api_4_Users)
test_5 = TestLoader().loadTestsFromTestCase(Test_Api_5_Logs)
test_6 = TestLoader().loadTestsFromTestCase(Test_Api_6_SensorSummary)
test_7 = TestLoader().loadTestsFromTestCase(Test_Api_7_BackgroundTasks)
test_8 = TestLoader().loadTestsFromTestCase(Test_Api_Main)

# run all tests in order (but test_7 is run first to issues with sensor ids)
suite = TestSuite([test_7, test_1, test_2, test_3, test_4, test_5, test_6, test_8])

runner = HTMLTestRunner(
    output="testing/output", report_name="API_test_report", combine_reports=True, add_timestamp=False, open_in_browser=False, report_title="API Test Report", descriptions=True, verbosity=2
)

runner.run(suite)
