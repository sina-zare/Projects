#print(name:=input("Name: "))
#print(age:=int(input("Age: ")))
#f= ["apple", "cherry", "banana", "kiwi"]
#num= int(input())
List=[]
print("I'm Asking you to make a list, I'll reverse it for you!")
while 1>0:
    continu= input("Continue Filling List? y/n  ").lower()
    if continu == "y":
        List.append(input("Enter list item: "))

    elif continu == "n":
        break
    else:
        print("Answer not valid!")
########
length= len(List)
ListRev= []
i= 1
########
while i != (length+1):
    ListRev.append(List[length - i])
    i+= 1
print("Here is the List you made: " + str(List))
print("And this is the Reversed List I made: " + str(ListRev))