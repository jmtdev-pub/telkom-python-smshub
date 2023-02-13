import logging
import sys
import smpplib.gsm
import smpplib.client
import smpplib.consts 
import urllib3
import urllib.parse
import datetime
import myModule


t = datetime.datetime.now()
logfile = t.strftime('%Y%m%d')
logging.basicConfig(
    filename=f'Log_{logfile}.log',
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logging.info("Connect")
generator = myModule.PersistentSequenceGenerator()
client = smpplib.client.Client('10.150.240.175', 15019, sequence_generator=generator, allow_unknown_opt_params=True)
# client = smpplib.client.Client('10.150.240.175', 15019)


def get_chatbot(from_number, message_to_send):
    try:
        url = "http://nbsc-ccp-lb:8443/cx/VSN/sms@System?vsDriver=1001351&User-Agent=IMified&SMSId=1643722175&from="+str(from_number)+"&msg="+message_to_send+"&userkey="+str(from_number)+"&ANI="+str(from_number)+""
        http = urllib3.PoolManager()
        response = http.request('GET', url)
        reply = response.data.decode()
        reply = urllib.parse.unquote_plus(reply)
        return reply
    except Exception as e:
        logging.info(str(e))


def onsend(pdu):
    try:
        logging.info(f"""ONSEND----sequence: {pdu.sequence}   message_id: {pdu.message_id}""")
    except Exception as e:
        logging.info(str(e))


def onrec(pdu):
    try:
        # logging.info(pdu.__dict__)
        destination_addr = pdu.destination_addr.decode("utf-8")
        source_addr = pdu.source_addr.decode("utf-8")
        short_message = pdu.short_message.decode("utf-8")
        logging.info(f"""ONREC----destination_addr: {destination_addr}   source_addr: {source_addr}   short_message: {short_message}   """)
        #######################################
        if not str(short_message).startswith("id:"):
            msg = get_chatbot(source_addr, short_message)
            # logging.info(msg)
            parts, encoding_flag, msg_type_flag = smpplib.gsm.make_parts(msg)
            for part in parts:
                pdu2 = client.send_message(
                    source_addr_ton=smpplib.consts.SMPP_TON_INTL,
                    source_addr=destination_addr,
                    dest_addr_ton=smpplib.consts.SMPP_TON_INTL,
                    destination_addr=source_addr,
                    short_message=part,
                    data_coding=encoding_flag,
                    esm_class=msg_type_flag,
                    registered_delivery=True,
                )        
    except Exception as e:
        logging.info(str(e))


logging.info("Start")
try:
    client.set_message_sent_handler(onsend)
    client.set_message_received_handler(onrec)
    client.connect()
    client.bind_transceiver(system_id='smshub', password='hub@sms')
    client.listen()
except Exception as e:
    logging.info(str(e))
logging.info("Ended")
