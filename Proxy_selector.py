import logging  # Import the logging module
from PyQt5.QtSql import QSqlDatabase, QSqlQuery
from requests import Session
from requests.exceptions import Timeout, ConnectionError
import time
import os
import sqlite3
import heapq  # For maintaining a priority queue

# Configure logging
logging.basicConfig(level=logging.ERROR)

def get_best_working_proxy(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Proxies")
        proxies = cursor.fetchall()
        total_proxies = len(proxies)
        best_proxies = []
        heapq.heapify(best_proxies)

        for index, proxy in enumerate(proxies):
            proxy_id, ip, port, username, password, _, _, errori = proxy
            start_time = time.time()
            with Session() as session:
                try:
                    proxy_dict = {'http': f'http://{username}:{password}@{ip}:{port}/'}
                    r = session.get('http://ipinfo.io/json', proxies=proxy_dict, timeout=5)
                    latency = time.time() - start_time
                    if r.status_code == 200:
                        print(f'Proxy {ip}:{port} is working with latency {latency} seconds.')
                        heapq.heappush(best_proxies, (latency, proxy))
                        cursor.execute('UPDATE Proxies SET Working=?, Errori=? WHERE ID=?', ('1', errori, proxy_id))
                        conn.commit()
                except (Timeout, ConnectionError) as e:
                    logging.error(f'Connection error or timeout with proxy {ip}:{port}: {e}')
                    cursor.execute('UPDATE Proxies SET Working=?, Errori=? WHERE ID=?', ('0', errori + 1, proxy_id))
                    conn.commit()
                    continue

        top_10_proxies = heapq.nsmallest(10, best_proxies)
        updated_proxies = []

        for latency, proxy in top_10_proxies:
            latencies = []
            for _ in range(5):
                start_time = time.time()
                with Session() as session:
                    proxy_dict = {'http': f'http://{proxy[3]}:{proxy[4]}@{proxy[1]}:{proxy[2]}/'}
                    session.get('http://ipinfo.io/json', proxies=proxy_dict, timeout=5)
                    latencies.append(time.time() - start_time)
            average_latency = sum(latencies) / len(latencies)
            updated_proxies.append((average_latency, proxy))

        if updated_proxies:
            best_proxy = min(updated_proxies, key=lambda x: x[0])[1]
            print(f'The best proxy is {best_proxy[1]}:{best_proxy[2]} with an average latency of {min(updated_proxies, key=lambda x: x[0])[0]} seconds.')
            return best_proxy
        else:
            print('No working proxy found.')
            return None
    except Exception as e:
        logging.error(f'General error in get_best_working_proxy: {e}')

if __name__ == '__main__':
    try:
        best_proxy = get_best_working_proxy()
        if best_proxy:
            print(f'The best proxy is: {best_proxy}')
        else:
            print('No working proxy found.')
    except Exception as e:
        logging.error(f'General error in main: {e}')