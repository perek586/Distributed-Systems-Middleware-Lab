# -----------------------------------------------------------------------------
# Distributed Systems (TDDD25)
# -----------------------------------------------------------------------------
# Author: Sergiu Rafiliu (sergiu.rafiliu@liu.se)
# Modified: 31 July 2013
#
# Copyright 2012 Linkoping University
# -----------------------------------------------------------------------------

"""Module for the distributed mutual exclusion implementation.

This implementation is based on the second Rikard-Agravara algorithm.
The implementation should satisfy the following requests:
    --  when starting, the peer with the smallest id in the peer list
        should get the token.
    --  access to the state of each peer (dictinaries: request, token,
        and peer_list) should be protected.
    --  the implementation should gratiously handle situations when a
        peer dies unexpectedly. All exceptions comming from calling
        peers that have died, should be handled such as the rest of the
        peers in the system are still working. Whenever a peer has been
        detected as dead, the token, request, and peer_list
        dictionaries should be updated acordingly.
    --  when the peer that has the token (either TOKEN_PRESENT or
        TOKEN_HELD) quits, it should pass the token to some other peer.
    --  For simplicity, we shall not handle the case when the peer
        holding the token dies unexpectedly.

"""

NO_TOKEN = 0
TOKEN_PRESENT = 1
TOKEN_HELD = 2


class DistributedLock(object):

    """Implementation of distributed mutual exclusion for a list of peers.

    Public methods:
        --  __init__(owner, peer_list)
        --  initialize()
        --  destroy()
        --  register_peer(pid)
        --  unregister_peer(pid)
        --  acquire()
        --  release()
        --  request_token(time, pid)
        --  obtain_token(token)
        --  display_status()

    """

    def __init__(self, owner, peer_list):
        self.peer_list = peer_list
        self.owner = owner
        self.time = 0
        self.token = None
        self.request = {}
        self.state = NO_TOKEN

    def _prepare(self, token):
        """Prepare the token to be sent as a JSON message.

        This step is necessary because in the JSON standard, the key to
        a dictionary must be a string whild in the token the key is
        integer.
        """
        return list(token.items())

    def _unprepare(self, token):
        """The reverse operation to the one above."""
        return dict(token)
        
    def _send_token(self):
        """Private method to send token if somebody has requested it. Returns True if token was sent"""
        peer_ids = list(self.request.keys())
        peer_ids.sort()
        peers = self.peer_list.get_peers()
        #We want to iterate from our ids index + 1 to our ids index - 1
        start = peer_ids.index(self.owner.id) + 1
        end = start + len(peer_ids) - 1
        
        self.token[self.owner.id] = self.time
        
        for index in range(start, end):
            index = index % len(peer_ids)
            id_to_check = peer_ids[index]
            if self.request[id_to_check] > self.token[id_to_check]:
                peers[id_to_check].obtain_token(self._prepare(self.token))
                self.state = NO_TOKEN
                self.token = None
                return True
        return False
        
    # Public methods

    def initialize(self):
        """ Initialize the state, request, and token dicts of the lock.

        Since the state of the distributed lock is linked with the
        number of peers among which the lock is distributed, we can
        utilize the lock of peer_list to protect the state of the
        distributed lock (strongly suggested).

        NOTE: peer_list must already be populated when this
        function is called.

        """
        self.peer_list.lock.acquire()
        try:
            peer_ids = list(self.peer_list.get_peers().keys())
            peer_ids.sort()
            if peer_ids[0] == self.owner.id:
                self.state = TOKEN_PRESENT
                self.token = {}
            else:
                self.state = NO_TOKEN
                
            for peer_id in peer_ids:
                self.request[peer_id] = 0
                if self.token != None:
                    self.token[peer_id] = 0
        finally:
            self.peer_list.lock.release()
            
    def destroy(self):
        """ The object is being destroyed.

        If we have the token (TOKEN_PRESENT or TOKEN_HELD), we must
        give it to someone else.

        """
        self.peer_list.lock.acquire()
        try:
            if self.state != NO_TOKEN:
                sent = self._send_token()
                
                if not sent and len(peers) != 1: #We send the token to the peer after us in a sorted list of peers
                    peers[(start+1)%len(peers)].obtain_token(self.token)
                    self.state = NO_TOKEN
                
        finally:
            self.peer_list.lock.release()
            
    def register_peer(self, pid):
        """Called when a new peer joins the system."""
        if self.state != NO_TOKEN:
            self.token[pid] = 0
        self.request[pid] = 0

    def unregister_peer(self, pid):
        """Called when a peer leaves the system."""
        if self.state != NO_TOKEN:
            del self.token[pid]
        del self.request[pid]

    def acquire(self):
        """Called when this object tries to acquire the lock."""
        print("Trying to acquire the lock...")
        self.time += 1
        self.peer_list.lock.acquire()
        try:
            if self.state == TOKEN_PRESENT:
                self.state = TOKEN_HELD
            elif self.state == NO_TOKEN:
                for peer in self.peer_list.get_peers().values():
                    peer.request_token(self.time, self.owner.id)
            else:
                print("Lock already acquired")
        finally:
            self.peer_list.lock.release()
        while self.state == NO_TOKEN:
            pass
        
    def release(self):
        """Called when this object releases the lock."""
        print("Releasing the lock...")
        self.time += 1
        self.peer_list.lock.acquire()
        try:
            if self.state == TOKEN_HELD:
                self.state = TOKEN_PRESENT
                self._send_token()
        finally:
            self.peer_list.lock.release()
                
    def request_token(self, time, pid):
        """Called when some other object requests the token from us."""
        self.time += 1
        self.request[pid] = time
        if self.state == TOKEN_PRESENT:
            self._send_token()
        
    def obtain_token(self, token):
        """Called when some other object is giving us the token."""
        print("Receiving the token...")
        self.time += 1
        self.token = self._unprepare(token)
        if self.request[self.owner.id] > self.token[self.owner.id]:
            self.state = TOKEN_HELD
        else:
            self.state = TOKEN_PRESENT

    def display_status(self):
        """Print the status of this peer."""
        self.peer_list.lock.acquire()
        try:
            nt = self.state == NO_TOKEN
            tp = self.state == TOKEN_PRESENT
            th = self.state == TOKEN_HELD
            print("State   :: no token      : {0}".format(nt))
            print("           token present : {0}".format(tp))
            print("           token held    : {0}".format(th))
            print("Request :: {0}".format(self.request))
            print("Token   :: {0}".format(self.token))
            print("Time    :: {0}".format(self.time))
        finally:
            self.peer_list.lock.release()
