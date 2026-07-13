import time
from DrissionPage import ChromiumPage

p = ChromiumPage()
p.get('https://sale.591.com.tw/home/house/detail/2/20165902.html')

t0 = time.time()
while p.ele('xpath://h1').text == '${title}' and time.time() - t0 < 5:
    time.sleep(0.1)

print('Time waited for title render:', time.time() - t0)
print('Text:', p.ele('xpath://h1').text)
p.quit()
