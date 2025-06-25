#Split a check including tax and tips
import sys

#Ask amount of payers
while True:
    try:
        eaters = int(input('How many people are paying? '))
        break
    except Exception as e:
        print('Enter an whole integer (etc 1, 67, 103)')

#Ask how much eat payer is paying
checklist = []
subtotal = 0
personum = 1
print('Enter following prices down to the penny for accuracy')
for eater in range(eaters):
    while True:
        try:
            price = float(input(f'Person {personum}: '))
            break
        except Exception as e:
            print('Enter a price (etc: .99, 5, 187.71)')
    checklist.append(price)
    subtotal += price
    personum += 1

#Quality check against already known values
sub = float(input('Enter Subtotal from check: '))
if subtotal != sub:
    print(f'Prices entered does not match subtotal on check. Calc-{subtotal} vs Check-{sub}')
    sys.exit()
rtotal = float(input('Enter Total: '))
total = float("{:.2f}".format(rtotal))

#Find tax rate and tax amount split
taxrate = ((total-sub)/sub)*100
rate = "{:.2f}".format(taxrate)
taxamt = float("{:.2f}".format(total-sub))
taxsplit = taxamt/eaters
print(f'Tax paid: {taxamt} at ~{rate}%')

#Ask and create tip %
while True:
    try:
        tip = float(input('What tip % do you want to give? '))
        break
    except Exception as e:
        print('Enter a just a number, no '%'')
tipp = tip/100

#Calculate off subtotal and display tip amount
tipamount = subtotal*tipp
tipsplit = tipamount/eaters
tipamt = float("{:.2f}".format(tipamount))
print(f'Total tip amount based off subtotal: {tipamt}')
print(f'Total with tip: {tipamt+total}')

#Display paysplit
personnum = 1
for eater in checklist:
    pay = "{:.2f}".format(eater+tipsplit+taxsplit)
    print(f'Person {personnum}: {pay}')
    personnum += 1
    
    #nikki 29.85
    #josh 29.85
    #Ayden 18.4
    #javid 35.85
    #T 19.90