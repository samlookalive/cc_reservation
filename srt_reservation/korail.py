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
from selenium.common.exceptions import ElementClickInterceptedException, StaleElementReferenceException, WebDriverException
import os
os.environ['WDM_SSL_VERIFY'] = '0'
#from srt_reservation.exceptions import InvalidStationNameError, InvalidDateError, InvalidDateFormatError, InvalidTimeFormatError
#from srt_reservation.validation import station_list
#from exceptions import InvalidStationNameError, InvalidDateError, InvalidDateFormatError, InvalidTimeFormatError
#from validation import station_list

chromedriver_path = r'C:\workspace\chromedriver.exe'

class KORAIL:
    def __init__(self, dpt_stn, arr_stn, dpt_year, dpt_month, dpt_day,  dpt_tm, num_trains_to_check=2, want_reserve=False):
        """
        :param dpt_stn: KORAIL 출발역
        :param arr_stn: KORAIL 도착역
        :param dpt_dt: 출발 날짜 YYYYMMDD 형태 ex) 20220115
        :param dpt_tm: 출발 시간 hh 형태, 반드시 짝수 ex) 06, 08, 14, ...
        :param num_trains_to_check: 검색 결과 중 예약 가능 여부 확인할 기차의 수 ex) 2일 경우 상위 2개 확인
        :param want_reserve: 예약 대기가 가능할 경우 선택 여부
        """
        self.login_id = '0960037025'
        self.login_psw = 'ghkrhr2ehd!'

        self.dpt_stn = dpt_stn
        self.arr_stn = arr_stn
        self.dpt_year = dpt_year
        self.dpt_month = dpt_month
        self.dpt_day = dpt_day
        self.dpt_tm = dpt_tm

        self.num_trains_to_check = num_trains_to_check
        self.want_reserve = want_reserve
        self.driver = None

        self.is_booked = False  # 예약 완료 되었는지 확인용
        self.cnt_refresh = 0  # 새로고침 회수 기록

        #self.check_input()

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
            self.driver = webdriver.Chrome(ChromeDriverManager().install())

    def login(self):
        self.driver.get('https://www.letskorail.com/korail/com/login.do')
        self.driver.implicitly_wait(15)
        self.driver.find_element(By.XPATH, '//*[@id="txtMember"]').send_keys(str(self.login_id))
        self.driver.find_element(By.XPATH, '//*[@id="txtPwd"]').send_keys(str(self.login_psw))
        self.driver.find_element(By.XPATH, '//*[@id="loginDisplay1"]/ul/li[3]/a/img').click()
        self.driver.implicitly_wait(5)
        return self.driver

    def check_login(self):
        menu_text = self.driver.find_element(By.CSS_SELECTOR, "#wrap > div.header.header-e > div.global.clear > div").text
        if "환영합니다" in menu_text:
            return True
        else:
            return False

    def go_search(self):
        # 기차 조회 페이지로 이동
        self.driver.get('https://www.letskorail.com/ebizprd/EbizPrdTicketpr21100W_pr21110.do')
        self.driver.implicitly_wait(5)

        # 출발지 입력
        elm_dpt_stn = self.driver.find_element(By.ID, 'start')
        elm_dpt_stn.clear()
        elm_dpt_stn.send_keys(self.dpt_stn)

        # 도착지 입력
        elm_arr_stn = self.driver.find_element(By.ID, 'get')
        elm_arr_stn.clear()
        elm_arr_stn.send_keys(self.arr_stn)

        # 출발 날짜 입력
        #elm_dpt_dt = self.driver.find_element(By.ID, "s_day")
        #self.driver.execute_script("arguments[0].setAttribute('style','display: True;')", elm_dpt_dt)
        Select(self.driver.find_element(By.XPATH, '//*[@id="s_month"]')).select_by_visible_text(self.dpt_month)
        Select(self.driver.find_element(By.XPATH, '//*[@id="s_day"]')).select_by_visible_text(self.dpt_day)

        # 출발 시간 입력
        #elm_dpt_tm = self.driver.find_element(By.ID, "dptTm")
        #self.driver.execute_script("arguments[0].setAttribute('style','display: True;')", elm_dpt_tm)
        Select(self.driver.find_element(By.XPATH, '//*[@id="s_hour"]')).select_by_value(self.dpt_tm)

        print("기차를 조회합니다")
        print(f"출발역:{self.dpt_stn} , 도착역:{self.arr_stn}\n날짜:{self.dpt_day}, 시간: {self.dpt_tm}시 이후\n{self.num_trains_to_check}개의 기차 중 예약")
        print(f"예약 대기 사용: {self.want_reserve}")

        self.driver.find_element(By.XPATH, '//*[@id="center"]/form/div/p/a/img').click()
        self.driver.implicitly_wait(5)
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

    def refresh_result(self):
        submit = self.driver.find_element(By.XPATH, "//input[@value='조회하기']")
        self.driver.execute_script("arguments[0].click();", submit)
        self.cnt_refresh += 1
        print(f"새로고침 {self.cnt_refresh}회")
        self.driver.implicitly_wait(10)
        time.sleep(0.5)

    def reserve_ticket(self, reservation, i):
        if "신청하기" in reservation:
            print("예약 대기 완료")
            self.driver.find_element(By.CSS_SELECTOR,
                                     f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({i}) > td:nth-child(8) > a").click()
            self.is_booked = True
            return self.is_booked
    def check_result(self):
        while True:
            for i in range(4, 4+1):
                num = (i*2) - 1
                try:
                    standard_seat = self.driver.find_element(By.CSS_SELECTOR, f"#tableResult > tbody > tr:nth-child({num}) > td:nth-child(6)").text
                    reservation = self.driver.find_element(By.CSS_SELECTOR, f"#tableResult > tbody > tr:nth-child({num}) > td:nth-child(7)").text
                except StaleElementReferenceException:
                    standard_seat = "매진"
                    reservation = "매진"
                print(standard_seat)
                if self.book_ticket(standard_seat, i):
                    return self.driver

                # 예약 대기 사용
                if self.want_reserve:
                    self.reserve_ticket(reservation, i)

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


if __name__ == "__main__":
    #korail_id = os.environ.get('0960037025')
    #korail_psw = os.environ.get('ghkrhr2ehd!')

    korail = KORAIL("조치원", "영등포", "2023", "3", "17", '17')
    korail.run('0960037025', 'ghkrhr2ehd!')

