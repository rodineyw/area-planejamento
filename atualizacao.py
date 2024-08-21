import schedule
import time


def atualizar_dados():
    print("Atualizando dados...")


# Agendar para executar a cada 30 minutos
schedule.every(30).minutes.do(atualizar_dados)

while True:
    schedule.run_pending()
    time.sleep(1)
