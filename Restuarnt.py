import simpy
import random

NUM_OF_SIM = 1
NUMBER_OF_MONTHS = 3
TIME_OF_SIM = NUMBER_OF_MONTHS * 30 * 24 * 60
TAXES = 0.14
WORK_TIME = 720
INTER_ARRIVAL = [0, 180]
RANDOM_SEED = 42
Arrive = [[0] * 30] * (NUMBER_OF_MONTHS)
ArriveSum = [0] * 30
waiterCapacity = 2
cookerCapacity = 3
waiterSalary = 1000
cookerSalary = 800
placeInstallation = 3000
averageProfit = 0
itemsPrice = [
    {"price": 1, "timeToCook": [5, 10]},
    {"price": 2, "timeToCook": [10, 15]},
    {"price": 3, "timeToCook": [10, 20]},
    {"price": 4, "timeToCook": [20, 30]},
    {"price": 5, "timeToCook": [20, 25]}
]
itemPercentage = [10, 20, 30, 30, 10]
numberOfCustomers = [20, 40, 30, 10]
numberOfItems = [40, 25, 25, 10]
customerClass = [70, 30]
waiterWaitTime = [2, 4]
profit = 0


class Restaurant:
    def __init__(self, env):
        self.state = True
        self.env = env
        self.waiters = simpy.PriorityResource(self.env, capacity=waiterCapacity)
        self.cookers = simpy.Resource(self.env, capacity=cookerCapacity)
        self.env.process(self.restaurantState())
        self.env.process(self.customerArrive())

    def startSimu(self):
        self.env.run(until=TIME_OF_SIM)

    def getReminderTime(self):
        # Calculate the reminder time for closure
        return WORK_TIME - (self.env.now % WORK_TIME)

    def restaurantState(self):
        while True:
            # Wait WORK_TIME to change restuarant state
            yield self.env.timeout(WORK_TIME)
            self.state = not (self.state)

    def customerArrive(self):
        i = 0
        # Generate Group of customers
        while True:
            # Check if Restuarant is open or not
            if not (self.state):
                yield self.env.timeout(1)
                continue

            # Get random number for inter-arrival time
            rand = random.randint(*INTER_ARRIVAL)
            # print("group {} inter-arrival {}".format(i, rand))

            if rand > self.getReminderTime():
                yield self.env.timeout(self.getReminderTime())
                continue
            # Wait for next Group
            yield self.env.timeout(rand)
            # Start Serving the Group
            self.env.process(self.Group(self.env.now, "group {}".format(i)))
            i += 1

    def Group(self, arrivalTime, name):
        # Random variables for number of customers
        rand = random.randint(0, 100)
        customers = self.getRandom(rand, numberOfCustomers)

        # Arrive[int(arrivalTime/43200)][int(arrivalTime/1440)%30] += customers
        ArriveSum[int(arrivalTime / 1440) % 30] += customers
        # Random variable of customers class
        rand = random.randint(0, 100)
        classPriority = self.getRandom(rand, customerClass)

        # Run waiter serve group process
        with self.waiters.request(priority=classPriority, preempt=True) as waiterReq:
            # wait for available waiter
            yield waiterReq

            # Random variable for waiter waiting time
            rand = random.randint(*waiterWaitTime)

            # Run Get order process
            self.env.process(self.getOrder(customers, name, rand))

    def getRandom(self, rand, array):
        sum = 0
        for i in range(len(array)):
            sum += array[i]
            if rand <= sum:
                return i + 1

    def getOrder(self, numberOfCustomers, name, waiterTime):
        ordersTime = []
        global profit
        for i in range(numberOfCustomers):
            # Random variable for number of items
            rand = random.randint(0, 100)
            itemCount = self.getRandom(rand, numberOfItems)

            # print("in {} the customer no. {} #of Items {}".format(name, i + 1, itemCount))
            for j in range(itemCount):
                # Random variable for selected item
                rand = random.randint(0, 100)
                item = self.getRandom(rand, itemPercentage)

                # print("in {} the customer no. {} and order no. {} is Item {}".format(name, i + 1, j + 1, item))
                profit += itemsPrice[item - 1]["price"]
                # Random variable for time to cook this item
                rand = random.randint(*itemsPrice[item - 1]["timeToCook"])
                ordersTime.append(rand)
                # print("in {} the customer no. {} and order no. {} will take {} to cook and the price is {}".format(name, i + 1, item, rand, itemsPrice[item - 1]["price"]))

        # wait waiter to take order
        yield self.env.timeout(waiterTime)

        # start cook the order
        self.env.process(self.cook(ordersTime))

    def cook(self, ordersTime):
        for order in ordersTime:
            with self.cookers.request() as cookerReq:
                # wait for available cooker
                yield cookerReq
                # wait for cook done
                yield self.env.timeout(order)


def netProfit():
    global profit
    profit /= 2
    profit -= NUMBER_OF_MONTHS * NUM_OF_SIM * (
                placeInstallation + (cookerSalary * cookerCapacity) + (waiterSalary * waiterCapacity))
    profit -= profit * TAXES


def sumOfCustomersPerDay():
    for i in range(30):
        print(ArriveSum[i])
        ArriveSum[i] /= (NUMBER_OF_MONTHS * NUM_OF_SIM)


random.seed(RANDOM_SEED)

