# -*- coding: utf-8 -*-
import os
import time
from random import randint
from datetime import datetime
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import ElementClickInterceptedException, StaleElementReferenceException, WebDriverException, NoSuchElementException
#from cc_reservation.exceptions import InvalidStationNameError, InvalidDateError, InvalidDateFormatError, InvalidTimeFormatError
#from cc_reservation.validation import station_list
from exceptions import InvalidStationNameError, InvalidDateError, InvalidDateFormatError, InvalidTimeFormatError
from validation import station_list
# for alert 처리
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.alert import Alert

chromedriver_path = r'C:\workspace\chromedriver.exe'

class SRT:
    def __init__(self, dpt_stn, arr_stn, dpt_dt, dpt_tm, num_trains_to_check=2, want_reserve=False):
        """
        :param dpt_stn: SRT 출발역
        :param arr_stn: SRT 도착역
        :param dpt_dt: 출발 날짜 YYYYMMDD 형태 ex) 20220115
        :param dpt_tm: 출발 시간 hh 형태, 반드시 짝수 ex) 06, 08, 14, ...
        :param num_trains_to_check: 검색 결과 중 예약 가능 여부 확인할 기차의 수 ex) 2일 경우 상위 2개 확인
        :param want_reserve: 예약 대기가 가능할 경우 선택 여부
        """
        self.login_id = None
        self.login_psw = None

        self.dpt_stn = dpt_stn
        self.arr_stn = arr_stn
        self.dpt_dt = dpt_dt
        self.dpt_tm = dpt_tm

        self.num_trains_to_check = num_trains_to_check
        self.want_reserve = want_reserve
        self.driver = None

        self.is_booked = False  # 예약 완료 되었는지 확인용
        self.cnt_refresh = 0  # 새로고침 회수 기록

        self.check_input()

    def check_input(self):
        if self.dpt_stn not in station_list:
            raise InvalidStationNameError(f"출발역 오류. '{self.dpt_stn}' 은/는 목록에 없습니다.")
        if self.arr_stn not in station_list:
            raise InvalidStationNameError(f"도착역 오류. '{self.arr_stn}' 은/는 목록에 없습니다.")
        if not str(self.dpt_dt).isnumeric():
            raise InvalidDateFormatError("날짜는 숫자로만 이루어져야 합니다.")
        try:
            datetime.strptime(str(self.dpt_dt), '%Y%m%d')
        except ValueError:
            raise InvalidDateError("날짜가 잘못 되었습니다. YYYYMMDD 형식으로 입력해주세요.")

    def set_log_info(self, login_id, login_psw):
        self.login_id = login_id
        self.login_psw = login_psw

    def run_driver(self):
        try:
            self.driver = webdriver.Chrome(executable_path=chromedriver_path)
        except WebDriverException:
            import os
            os.environ['WDM_SSL_VERIFY'] = '0'
            self.driver = webdriver.Chrome(ChromeDriverManager().install())

    def login(self):
        self.driver.get('https://www.sejongcc.com/login/login.do')
        self.driver.implicitly_wait(15)
        self.driver.find_element(By.ID, 'usrId').send_keys(str(self.login_id))
        self.driver.find_element(By.ID, 'usrPwd').send_keys(str(self.login_psw))
        self.driver.find_element(By.CLASS_NAME, 'bt_login').click()
        self.driver.implicitly_wait(5)
        time.sleep(1)
        Alert(self.driver).accept()
        '''
        try:
              WebDriverWait(self.driver, 3).until(EC.alert_is_present())
              result = self.driver.switch_to_alert
              print(result.text)
              result.dismiss()
              result.accept()
              return self.driver
        except:
              print("no alert")
        '''
    def check_login(self):
        menu_text = self.driver.find_element(By.CSS_SELECTOR, "#wrap > div.header.header-e > div.global.clear > div").text
        if "환영합니다" in menu_text:
            return True
        else:
            return False

    def go_search(self):
        # 기차 조회 페이지로 이동
        self.driver.get('https://www.sejongcc.com/reservation/real_reservation.do')
        self.driver.implicitly_wait(5)
        self.driver.find_element(By.XPATH, '//*[@id="calendar_view_ajax_2"]/table/tbody/tr[3]/td[2]/a').click()
        # 해당하는 날짜가 클릭 가능한지 확인?
        time.sleep(1)

    def book_ticket(self, standard_seat, i):
        # standard_seat는 일반석 검색 결과 텍스트

        if "예약하기" in standard_seat:
            print("예약 가능 클릭")

            # Error handling in case that click does not work
            try:
                self.driver.find_element(By.CSS_SELECTOR,
                                         f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({i}) > td:nth-child(7) > a").click()
            except ElementClickInterceptedException as err:
                print(err)
                self.driver.find_element(By.CSS_SELECTOR,
                                         f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({i}) > td:nth-child(7) > a").send_keys(
                    Keys.ENTER)
            finally:
                self.driver.implicitly_wait(3)

            # 예약이 성공하면
            if self.driver.find_elements(By.ID, 'isFalseGotoMain'):
                self.is_booked = True
                print("예약 성공")
                return self.driver
            else:
                print("잔여석 없음. 다시 검색")
                self.driver.back()  # 뒤로가기
                self.driver.implicitly_wait(5)

    def book_firsttime(self, revtime, revlen):
        # reservtime 에는 i개의 예약가능 시간
        # print("예약 클릭")
        # Error handling in case that click does not work
        if revtime[0] != 0:
            try:
                self.driver.find_element(By.XPATH, f'//*[@id="timeresbtn_{revtime[0]}_{revtime[1]}{revtime[2]}"]').click()
                self.driver.implicitly_wait(20)
                captcha = self.driver.find_element(By.XPATH, '//*[@id="golfdataform"]/table[3]/tbody/tr[1]/td').text
                input = self.driver.find_element(By.NAME, "certNoChk")
                input.clear()
                input.send_keys(str(captcha))
                self.driver.implicitly_wait(10)
                time.sleep(5)
            except NoSuchElementException:
                print("Element 찾지 못함")
            except ElementClickInterceptedException as err:
                print(err)
                self.driver.implicitly_wait(3)
            finally:
                self.driver.implicitly_wait(3)
            # TODO : 예약 성공 확인 부분 만들어야됨
            self.is_booked = True
            print("예약성공")
        
    def refresh_result(self):
        self.driver.find_element(By.XPATH, '//*[@id="calendar_view_ajax_2"]/table/tbody/tr[3]/td[2]/a').click()
        self.cnt_refresh += 1
        print(f"새로고침 {self.cnt_refresh}회")
        self.driver.implicitly_wait(10)
        time.sleep(0.5)

    def check_result(self):
        while True:
            #for i in range(1, self.num_trains_to_check+1):
            #self.is_booked = True
            reservtime = [0, 0, 0]
            for i in range(1, 50):
                try:
                    #standard_seat = self.driver.find_element(By.CSS_SELECTOR, '//*[@id="tab0"]/table/tbody/tr[1]/td[3]').text
                    rvtime = self.driver.find_element(By.XPATH, f'//*[@id="tab0"]/table/tbody/tr[{i}]/td[3]').text.split(':', 2)
                    csname = self.driver.find_element(By.XPATH, f'//*[@id="tab0"]/table/tbody/tr[{i}]/td[2]').text
                    if 8 <= int(rvtime[0]) <= 9 :
                        if csname == "세종" :
                            csnum = 1
                        elif csname == "행복" :
                            csnum = 2
                        else :
                            csnum = 0
                        reservtime[0] = (csnum)
                        reservtime[1] = (rvtime[0])
                        reservtime[2] = (rvtime[1])
                        break
                except NoSuchElementException:
                    #print("예약 가능 리스트 없음")
                    break

            if self.book_firsttime(reservtime, i):
                return self.driver
            
            if self.is_booked:
                return self.driver

            else:
                time.sleep(randint(2, 4))
                self.refresh_result()

    def run(self, login_id, login_psw):
        self.run_driver()
        self.set_log_info(login_id, login_psw)
        self.login()
        self.go_search()
        self.check_result()

srt_id = 'hoyoun100'
srt_psw = 'rlaghdus0509$'
srt = SRT("동탄", "동대구", "20230322", "08")

srt.run(srt_id, srt_psw)
