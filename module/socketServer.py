import socketserver
import sys


#data를 받으면 txt파일로 저장하기
class Server(socketserver.BaseRequestHandler):

    def handle(self):
        print('client address  :{0}\n'.format(self.client_address[0]))

        while True:
            try:
                sock = self.request
                buf = sock.recv(1024)  # type : bytes
                if len(buf) > 0:
                    # 1. sensor data 를 받아옴
                    result_str = str(buf, encoding='utf-8')
                    if result_str in 'Measure file':
                        print('Measure')

                    elif result_str in 'finish':
                        sock.close()
                        print('socket disconnect\n')
                        print(self.socket)
                        break
                    else:
                        print(result_str)  # log 기록

                else:
                    break
            except Exception:
                sock.close()
                print('socket exception disconnect\n')
                break



        '''

        sock.close()
        print('socket disconnect\n')


        #client에게 data보내기

        sock.send(buf)
        print('송신:{0}'.format(rec))

        sock.close()
        print('socket server disconnect')

        '''



'''
if __name__ == '__main__':

    #ip = '192.168.0.2'

    #port = 9002

    #ip = '127.0.0.1'

    #port = 9999

    ip = '127.0.0.1'
    port = 9999

    try:
        print(type(ip))
        server = socketserver.TCPServer((ip, port), Server)
        print('start...')
        print('server address  :{0}'.format(ip))
        server.serve_forever()
    except:
        print('check ipconfig ip')

    server.server_close()
    print('server close')


'''

