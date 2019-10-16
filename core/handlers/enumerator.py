#!/usr/bin/env python3

# Based on: https://bitbucket.org/grimhacker/office365userenum/

import sys
import signal
import urllib3
import aiohttp
import asyncio
from core.utils.config import *
from core.utils.helper import *
from core.utils.taskpool import *
from core.utils.colors import text_colors
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Enumerator:
    """ Perform user enumeration using Microsoft Server ActiveSync """

    valid_accts = []  # Valid account storage
    helper = Helper() # Helper functions

    def __init__(self, args):
        self.args   = args
        self.config = activesync
        self.task_limit = self.args.limit

    def shutdown(self, key=False):
        # Print new line after ^C
        msg = '\n[*] Writing valid accounts found to file \'%svalid_accts\'...' % self.args.output
        if key:
            msg  = '\n[!] CTRL-C caught.' + msg

        print(msg)
        self.helper.write_data(self.valid_accts, "%s/valid_accts.txt" % (self.args.output))


    async def run(self, userlist, password="Password1"):
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=None, ssl=False)) as session,\
            TaskPool(self.task_limit) as tasks:
            for user in userlist:
                await tasks.put(self.enum(session, user, password))


    async def enum(self, session, user, password):
        """ Enumerate users on Microsoft using Microsoft Server ActiveSync """
        try:

            headers["MS-ASProtocolVersion"] = "14.0"
            email = self.helper.check_email(user, self.args.domain)
            auth  = (email, password)
            async with session.options(
                        self.config["url"],
                        auth=aiohttp.BasicAuth(email, password),
                        headers=headers,
                        proxy=self.args.proxy,
                        timeout=self.args.timeout
                    ) as response:

                status = response.status
                if status in [200, 401, 403]:
                    print("[%s%s-%d%s] %s%s" % (text_colors.green, "VALID_USER", status, text_colors.reset, email, self.helper.space))
                    self.valid_accts.append(user)

                elif status == 404 and "X-CasErrorCode" in response.headers.keys() and response.headers["X-CasErrorCode"] == "UserNotFound":
                    print("[%s%s%s] %s%s\r" % (text_colors.red, "INVALID_USER", text_colors.reset, email, self.helper.space), end='\r')

                else:
                    print("[%s%s%s] %s%s\r" % (text_colors.yellow, "UNKNOWN", text_colors.reset, email, self.helper.space), end='\r')

                await response.text()

        except Exception as e:
            if self.args.debug: print("\n[ERROR] %s" % e)
            pass