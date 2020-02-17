#!/usr/bin/python

# This is a dummy peer that just illustrates the available information your peers 
# have available.

# You'll want to copy this file to AgentNameXXX.py for various versions of XXX,
# probably get rid of the silly logging messages, and then add more logic.

import random
import logging

from messages import Upload, Request
from util import even_split
from peer import Peer

class matesTyrant(Peer):
    def post_init(self):
        print "post_init(): %s here!" % self.id
        self.dummy_state = dict()
        self.dummy_state["cake"] = "lie"
    
    def requests(self, peers, history):
        """
        peers: available info about the peers (who has what pieces)
        history: what's happened so far as far as this peer can see

        returns: a list of Request() objects

        This will be called after update_pieces() with the most recent state.
        """
        needed = lambda i: self.pieces[i] < self.conf.blocks_per_piece
        needed_pieces = filter(needed, range(len(self.pieces)))
        np_set = set(needed_pieces)  # sets support fast intersection ops.


        logging.debug("%s here: still need pieces %s" % (
            self.id, needed_pieces))

        logging.debug("%s still here. Here are some peers:" % self.id)
        for p in peers:
            logging.debug("id: %s, available pieces: %s" % (p.id, p.available_pieces))

        logging.debug("And look, I have my entire history available too:")
        logging.debug("look at the AgentHistory class in history.py for details")
        logging.debug(str(history))

        #  find how many of each
        total_piece_dict = {}
        for peer in peers:
            peer_set = set(peer.available_pieces)
            for piece in peer_set:
                if piece not in total_piece_dict.keys():
                    total_piece_dict[piece] = [1, [peer.id]]
                else:
                    total_piece_dict[piece][0] += 1
                    total_piece_dict[piece][1].append(peer.id)


        '''
        #  keeps track of 
        all_pieces = {}
        for peer in peers:
            for piece in peer.available_pieces:
                if piece in all_pieces.keys():
                    all_pieces[piece] += 1
                else:
                    all_pieces[piece] = 1
        '''
        requests = []   # We'll put all the things we want here
        # Symmetry breaking is good...
        random.shuffle(needed_pieces)
        
        # Sort peers by id.  This is probably not a useful sort, but other 
        # sorts might be useful
        peers.sort(key=lambda p: p.id)
        # request all available pieces from all peers!
        # (up to self.max_requests from each)
        for peer in peers:
            # what peer has got
            av_set = set(peer.available_pieces)
            # what peer needs + what is available
            isect = av_set.intersection(np_set)

            # picking all the pieces for what P needs
            if self.max_requests >= len(isect):
                for piece_id in isect:
                    start_block = self.pieces[piece_id]
                    r = Request(self.id, peer.id, piece_id, start_block)
                    requests.append(r)
            else:
                # if you can't request all of the pieces
                #  pick the rarest first pieces
                #  check who has what pieces that you need

                missing_piece_list = []
                for piece_id in isect:
                    missing_piece_list.append((total_piece_dict[piece_id][0], piece_id))

                # sort the missing pieces by rarity
                missing_piece_list.sort()

                # how rare is rare
                rare_count = missing_piece_list[0][0]

                # finding all pieces of "rare" count
                rare_pieces = []
                for rare in missing_piece_list:
                    if rare[0] == rare_count:
                        rare_pieces.append(rare[1])

                # so every time you do it, you don't look for the same piece every time
                random.shuffle(rare_pieces)

                # getting everyone else in the list
                everyone_else = []
                for not_rare in missing_piece_list[len(rare_pieces):]:
                    everyone_else.append(not_rare[1])

                # newly combined list of rare_pieces first then every other piece
                budget_list = rare_pieces + everyone_else

                for piece_id in budget_list[:self.max_requests]:
                    start_block = self.pieces[piece_id]
                    r = Request(self.id, peer.id, piece_id, start_block)
                    requests.append(r)

                '''
                for piece_id in missing_piece_list[:self.max_requests]:
                    start_block = self.pieces[piece_id]
                    r = Request(self.id, peer.id, piece_id, start_block)
                    requests.append(r)
                '''

                # n = min(self.max_requests, len(isect))
                # More symmetry breaking -- ask for random pieces.
                # This would be the place to try fancier piece-requesting strategies
                # to avoid getting the same thing from multiple peers at a time.
                # for piece_id in random.sample(isect, n):
                # aha! The peer has this piece! Request it.
                # which part of the piece do we need next?
                # (must get the next-needed blocks in order)
                #     start_block = self.pieces[piece_id]
                #     r = Request(self.id, peer.id, piece_id, start_block)
                #     requests.append(r)
            # print(requests)
            return requests

    def uploads(self, requests, peers, history):
        """
        requests -- a list of the requests for this peer for this round
        peers -- available info about all the peers
        history -- history for all previous rounds

        returns: list of Upload objects.

        In each round, this will be called after requests().
        """
        uploads = []
        round = history.current_round()
        logging.debug("%s again.  It's round %d." % (
            self.id, round))
        # One could look at other stuff in the history too here.
        # For example, history.downloads[round-1] (if round != 0, of course)
        # has a list of Download objects for each Download to this peer in
        # the previous round.

        if len(requests) == 0:
            logging.debug("No one wants my pieces!")
            chosen = []
            bws = []
        else:
            # logging.debug("Still here: uploading to a random peer")
            # change my internal state for no reason
            self.dummy_state["cake"] = "pie"
            '''
            request = random.choice(requests)
            chosen = [request.requester_id]
            # Evenly "split" my upload bandwidth among the one chosen requester
            bws = even_split(self.up_bw, len(chosen))
            '''

            ratios = []

            if round == 0:
                download = []
                upload = []
                slots = 5
                # determining the ratio of peers
                for i in range(len(peers)):
                    upload.append(self.up_bw/(len(peers)-1))
                    download.append(peers[i].up_bw/slots)
                    ratios.append((float(download[i]/upload[i]), peers.id))

            else: # past the first round
                # download history of last round
                download_history = history.downloads[round-1]
                history_d = {}
                # print(download_history)
                for download in download_history:
                    download_id = download.from_id
                    if download not in history_d.keys():
                        history_d[download_id] = download.blocks
                    else:
                        history_d[download_id] += download.blocks

                # upload history of last round
                upload_history = history.uploads[round-1]
                history_u = {}

                for upload in upload_history:
                    upload_id = upload.from_id
                    if upload_id not in upload_history:
                        history_u[upload_id] = upload.bw
                    else:
                        history_u[upload_id] += upload.bw

                d = {}
                for peer in peers:
                    if peer.id not in history_d.keys():
                        last_download = len(peer.available_pieces) / round
                        # 5a of page 120 algo
                        if peer.id not in history_u.keys():
                            last_upload = self.up_bw / (len(peers) - 1)
                        else:
                            last_upload = history_u[peer.id] * (1 + 0.2)
                    else:
                        last_download = history_d[peer.id]
                        # r is 3 periods
                        rounds = [False, False, False]
                        if round >= 3:
                            for i in range(3):
                                hist_d = history.downloads[round - 1 - i]
                                for h in hist_d:
                                    if peer.id == h.from_id:
                                        rounds[i] = True

                        if peer.id not in history_u.keys():
                            last_upload = self.up_bw / (len(peers) - 1)
                        else:
                            last_upload = history_u[peer.id]

                        #  5c of page 120 algo
                        if (rounds[0] is True) and (rounds[1] is True) and (rounds[2] is True):
                            last_upload *= 0.9

                    d[peer.id] = [last_download, last_upload]
            rank = []
            for peer in d.keys():
            #     print(peer)
                rank.append((float(d[peer][0]/d[peer][1]), d[peer][1], peer))

            rank.sort()
            rank.reverse()

            cap = self.up_bw
            # print("cap is {0}".format(cap))
            count = 0
            while cap > 0:
                # print("---")
                if count <= len(rank) - 1:
                    # print("----")
                    if cap - rank[count][1] > 1:
                        uploads.append(Upload(self.id, rank[count][2], rank[count][1]))
                    cap -= rank[count][1]
                    count += 1
                else:
                    break



        # create actual uploads out of the list of peer ids and bandwidths
        '''
        uploads = [Upload(self.id, peer_id, bw)
                   for (peer_id, bw) in zip(chosen, bws)]
        '''
        # print(uploads)
        return uploads
