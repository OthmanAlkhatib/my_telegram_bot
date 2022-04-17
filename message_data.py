import datetime


class ReminderData:

    def __init__(self, row, time):
        self.reminder_id, self.chat_id, self.message, self.time, self.fired = row
        if time != -1:
            self.time = time

    def __repr__(self):
        return "Message: {0}; At Time: {1}".format(self.message, self.time.strftime('%d/%m/%Y %H:%M'))

    def should_be_fired(self):
        return self.fired is False and datetime.datetime.today() >= self.time
