import re


 



def parseLangue(langue: str ):
  return re.sub(r"[, ]", "", langue)



def findInLangue(langue: str): 

  current = ""
  langues = []

  for index in reversed(range(len(langue))):
    current = current + langue[index]
    if langue[index].isupper():
      reverse = reverseString(current)
      langues.append(reverse)
      current = ""
  return langues


def reverseString(langue: str):
  return langue[::-1]

def findUpperCase(langue: str):
  upper = []
  for char in langue:
    if char.isupper():
      upper.append( len(langue) - char)
  return upper


def findUniqueInArray(langues):
  unique = []
  for item in langues:
    if item not in unique:
      unique.append(item)
  return unique

# def getList(data: pd.DataFrame):
#   block = 10
#   langueArray = []
#   for i in range(len(data)):
#     location = data.loc[i, "LANGUES"]
#     if(type(location) == str):
#       langue = parseLangue(location)
#       langues = findInLangue(langue)
#       langueArray.extend(langues)

  

  print(findUniqueInArray(langueArray))




def main():
    lines = "AnglaisBulgareCroateEspagnol , CastillanFrançaisSerbo-croate"

    print(findInLangue(parseLangue(lines)))



main()