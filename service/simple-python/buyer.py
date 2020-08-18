#!/usr/bin/env python3
"""Simple Buyer example.
"""

import binascii
import os

import txaio
txaio.use_twisted()

from autobahn.wamp.types import SubscribeOptions
from autobahn.twisted.component import Component, run
from autobahn.twisted.xbr import SimpleBuyer

DEFAULT_AUTHID = 'team2'
DEFAULT_TICKET = 'cabbage peas onion eggplant'

comp = Component(
    transports=os.environ.get('XBR_INSTANCE', 'wss://continental2.crossbario.com/ws'),
    realm=os.environ.get('XBR_REALM', 'realm1'),
    authentication={
        'ticket': {
            'authid': os.environ.get('XBR_AUTHID', DEFAULT_AUTHID),
            'ticket': os.environ.get('XBR_TICKET', DEFAULT_TICKET),
        },
    },
    extra={
        'market_maker_adr': os.environ.get('XBR_MARKET_MAKER_ADR', '0x3e5e9111ae8eb78fe1cc3bb8915d5d461f3ef9a9'),
        'buyer_privkey': os.environ.get('XBR_BUYER_PRIVKEY', '0x2e6beb0073c9f6a13137f9637937e18b98d3a7ba0cfed52f1482249f5a8e51f0'),
    }
)


@comp.on_join
async def joined(session, details):
    print('Buyer session joined', details)

    market_maker_adr = binascii.a2b_hex(session.config.extra['market_maker_adr'][2:])
    print('Using market maker adr:', session.config.extra['market_maker_adr'])

    buyer_privkey = binascii.a2b_hex(session.config.extra['buyer_privkey'][2:])

    max_price = 100 * 10 ** 18
    buyer = SimpleBuyer(market_maker_adr, buyer_privkey, max_price)
    balance = await buyer.start(session, details.authid)
    balance = int(balance / 10 ** 18)
    print("Remaining balance: {} XBR".format(balance))

    async def on_event(key_id, enc_ser, ciphertext, details=None):
        try:
            payload = await buyer.unwrap(key_id, enc_ser, ciphertext)
        except Exception as e:
            print(e)
            session.leave()
        else:
            print('Received event {}:'.format(details.publication), payload)
            print(payload.__class__)

    await session.subscribe(on_event, "com.conti.hackathon.team2", options=SubscribeOptions(details=True, match='prefix'))


if __name__ == '__main__':
    run([comp])
