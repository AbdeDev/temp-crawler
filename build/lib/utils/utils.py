from selenium import webdriver
import re
import dateparser
import phonenumbers

def stripArray(arr):
  result = []
  for item in arr:
    result.append(item.strip())
  return result



def preparseAddress(arr):
  return findAddressWithPostalCode(removeBlankSpace(" ".join(arr).split(" ")))

def findAddressWithPostalCode(arr):
  data = {
    "street": None,
    "cp": None,
    "city": None
  }
 
  index = findPostalCode(arr)

  if index != None:
    street = arr[:index]
    cpCity = arr[index:]

    data["street"] = removeBlanckFromString(recreateString(street))
    data["city"] = removeBlanckFromString(recreateString(cpCity[1:]))
    data["cp"] = cpCity[0]

  return data



def findPostalCode(arr):
  for i in range(len(arr)):
    template = re.match('\d{5}', arr[i])
    if template:
      return i

def defaultAddress(): 
  return {
    "street": None,
    "city": None,
    "cp": None
  }

def removeBlanckFromString(string: list):
  return recreateString(removeBlankSpace(string.split(" ")))


def removeOtherChar(arr):
  result = []
  for item in arr:
    result.append(item.replace("\t", "").replace("\n", "").replace("\r", ""))
  return result

def removeBlankSpace(arr):
  result = []
  for item in arr:
    if item != "":
      result.append(item)
  return result


def removeSpace(arr):
    result = []
    for item in arr:
      if item != " ":
        result.append(item)
    return result


def recreateString(arr):
  result = ""
  for i in range(len(arr)):
    if i < len(arr) - 1:
      result += arr[i] + " "
    else:
      result += arr[i]
  return result

def toText(soup):
  result = ""
  for item in soup:
    result += str(item)
  return result


def parseCollapsedString(arr, word):

  listing = list(arr)
  itemStart = []
  for match in re.finditer(word, arr):
        itemStart.append(match.start())
        
  for index, i in enumerate(itemStart):
    listing.insert(index + i, ";")
  listing = "".join(listing)
  return listing

def getName(arr):
  data = {
    "firstName": "",
    "lastName": ""
  }
  for parts in arr:
    if len(parts) > 2:
      allUpper = re.findall(r'^[A-Z-\s]*$', parts)
      if allUpper:
        data["lastName"]  +=  parts + " "
      if parts[0].isupper() and parts[1:].islower():
        data["firstName"] += parts  + " "

      data["firstName"] = data["firstName"]
      data["lastName"] = data["lastName"]
  
  return data



def parseLangue(arr):
  result = ""
  for i in range(len(arr)):
    if i < len(arr) - 1:
      result += arr[i] + ";"
    else:
      result += arr[i]
  return result



def seleniumBrowser(headless=True):
  options = webdriver.ChromeOptions()
  options.add_argument('--ignore-certificate-errors')
  options.add_argument('--incognito')
  if  headless:
    options.add_argument('--headless')
  browser = webdriver.Chrome(options=options)
  return browser

def parserDate(date: str):
  parsing =  dateparser.parse(date)
  if parsing != None:
    return parsing.date().strftime("%d/%m/%Y")
  return None

  
def parsePhoneFax(telecom: str):
    if len(telecom) <= 12 and len(telecom) >= 10:
      try:
        phoneNumber = phonenumbers.parse(telecom, "FR")
        return phonenumbers.format_number(phoneNumber, phonenumbers.PhoneNumberFormat.INTERNATIONAL)  
      except TypeError as e:
        print(e)
        return None
    return None