#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      mpiwrapper.py
#  brief:     Defines mpi routines for pNbody
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################



import numpy as np
from . import libutil
import sys


class myMPI:
    def __init__(self):
        pass


try:
    from mpi4py import MPI

    comm = MPI.COMM_WORLD
    comm_self = MPI.COMM_SELF
    ThisTask = comm.Get_rank()
    NTask = comm.Get_size()
    Procnm = MPI.Get_processor_name()
    Rank = ThisTask
except BaseException:
    MPI = myMPI()
    MPI.sum = np.sum
    MPI.SUM = MPI.sum
    ThisTask = 0
    NTask = 1
    Rank = ThisTask
    Procnm = ""


def mpi_IsMaster():
    return ThisTask == 0


def mpi_Rank():
    return ThisTask


def mpi_ThisTask():
    return ThisTask


def mpi_NTask():
    return NTask


def mpi_barrier():
    if NTask > 1:
        comm.barrier()
    else:
        pass

#####################################
#
# Output functions
#
#####################################


def mpi_iprint(*obj):
    """
    Print, including info on node.
    """
    print("[%d] : " % ThisTask, *obj)


def mpi_pprint(*obj):
    """
    Synchronized print.
    """
    if NTask > 1:
        comm.barrier()
    print(*obj)


def mpi_rprint(*obj):
    """
    Rooted print.
    """
    if mpi_IsMaster():
        print(*obj)


#####################################
#
# communication functions
#
#####################################


def mpi_send(x, dest):
    """
    Send x to node dest.
    When there is only one is defined, it does nothing.
    """

    if NTask > 1:
        return comm.send(x, dest=dest)
    else:
        pass


def mpi_recv(source):
    """
    Return a variable sent by node \\var{source}.
    When there is only one is defined, it does nothing.

    """
    if NTask > 1:
        return comm.recv(source=source)
    else:
        pass


def mpi_sendrecv(x, dest, source):
    """
    """
    if NTask > 1:
        return comm.sendrecv(x, dest=dest, source=source)
    else:
        pass


def mpi_reduce(x, root=0, op=MPI.SUM):
    """
    Reduce x from all node only for root.
    When there is only one is defined, the function return x.
    """

    if NTask > 1:
        sx = comm.reduce(x, op=op, root=root)
    else:
        sx = x

    return sx


def mpi_allreduce(x, op=MPI.SUM):
    """
    Reduce x from all node for all nodes.
    When there is only one is defined, the function return x.
    """

    if NTask > 1:
        sx = comm.allreduce(x, op=op)
    else:
        sx = x

    return sx


def mpi_bcast(x, root=0):
    """
    Broadcast from node root the variable x.
    When there is only one is defined, it simplay returns x.
    """

    if NTask > 1:
        x = comm.bcast(x, root=root)
    else:
        x = x

    return x


def mpi_gather(x, root=0):
    """
    Gather x from all nodes to node dest.
    Returns a list.
    """

    if NTask > 1:
        x = comm.gather(x, root=root)
    else:
        x = [x]

    return x


def mpi_allgather(x):
    """
    Gather x from all to all.
    Returns a list.
    """

    if NTask > 1:
        x = comm.allgather(x)
    else:
        x = [x]

    return x


def mpi_AllgatherAndConcatArray(vec):
    """
    AllGather array vec and concatenate it in a unique array
    (concatenation order is reversed).
    """

    if NTask > 1:

        vec_all = np.array([], vec.dtype)
        if vec.ndim == 1:
            vec_all.shape = (0,)
        else:
            vec_all.shape = (0, vec.shape[1])

        if ThisTask == 0:

            for Task in range(NTask - 1, -1, -1):

                if Task != 0:
                    v = comm.recv(source=Task)
                    vec_all = np.concatenate((vec_all, v))
                else:
                    vec_all = np.concatenate((vec_all, vec))

        else:
            comm.send(vec, dest=0)

        # send to everybody
        xi = comm.bcast(vec_all)

        return xi

    else:
        return vec


#####################################
#
# array functions
#
#####################################


def mpi_sum(x):
    """
    Sum elements of array x.
    """

    if NTask > 1:
        sx = comm.allreduce(np.sum(x), op=MPI.SUM)
    else:
        sx = np.sum(x)

    return sx


def mpi_min(x):
    """
    Minimum element of array x.
    """

    if NTask > 1:
        mx = comm.allreduce(min(x), op=MPI.MIN)
    else:
        mx = min(x)

    return mx


def mpi_max(x):
    """
    Maximum element of array x.
    """

    if NTask > 1:
        mx = comm.allreduce(max(x), op=MPI.MAX)
    else:
        mx = max(x)

    return mx


def mpi_mean(x):
    """
    Mean of elements of array x.
    """

    if NTask > 1:
        sm = comm.allreduce(np.sum(x), op=MPI.SUM)
        sn = comm.allreduce(len(x), op=MPI.SUM)
        mn = sm / sn
    else:
        mn = x.mean()

    return mn


def mpi_len(x):
    """
    Length of array x.
    """

    if NTask > 1:
        ln = comm.allreduce(len(x), op=MPI.SUM)
    else:
        ln = len(x)

    return ln


def mpi_arange(n):
    """
    Create an integer array containing elements from 0 to n
    spread over all nodes.
    """

    if NTask > 1:
        ns = np.array(comm.allgather(n))
        c = ((NTask - 1 - ThisTask) > np.arange(len(ns) - 1, -1, -1))
        i = np.sum(ns * c)
        v = np.arange(i, i + ns[ThisTask])
    else:
        v = np.arange(n)

    return v


def mpi_sarange(npart_all):
    """
    Create an integer array containing elements from 0 to n,
    spreaded over all nodes. The repartition of elements and
    type of elements over nodes is given by the array npart_all

    """

    npart = npart_all[ThisTask]

    if NTask > 1:
        v = np.array([], int)
        o = 0

        for i in np.arange(len(npart)):

            # number of particles of this type for this proc
            n = npart_all[ThisTask, i]
            n_tot = np.sum(npart_all[:, i])

            ns = np.array(comm.allgather(n))
            c = ((NTask - 1 - ThisTask) > np.arange(len(ns) - 1, -1, -1))
            j = np.sum(ns * c)
            vj = np.arange(o + j, o + j + ns[ThisTask])
            v = np.concatenate((v, vj))

            o = o + n_tot

    else:
        n = np.sum(np.ravel(npart))
        v = np.arange(n)

    return v


def mpi_argmax(x):
    """
    Find the arument of the amximum value in x.

    idx = (p,i)  : where i = index in proc p

    """

    if NTask > 1:
        # 1) get all max and all argmax
        maxs = np.array(comm.allgather(max(x)))
        args = np.array(comm.allgather(np.argmax(x)))

        # 2) choose the right one
        p = np.argmax(maxs)	  # proc number
        i = args[p] 	  # index in proc p

    else:
        p = 0
        i = np.argmax(x)

    return p, i


def mpi_argmin(x):
    """
    Find the arument of the maximum value in x.
    idx = (p,i)  : where i = index in proc p

    """

    if NTask > 1:
        # 1) get all mins and all argmins
        mins = np.array(comm.allgather(min(x)))
        args = np.array(comm.allgather(np.argmin(x)))

        # 2) choose the right one
        p = np.argmin(mins)  # proc number
        i = args[p]		# index in proc p

    else:
        p = 0
        i = np.argmin(x)

    return p, i


def mpi_getval(x, idx):
    """
    Return the value of array x corresponding to the index idx.

    idx = (p,i)  : where i = index in proc p
    equivalent to x[i] from proc p

    """

    p = idx[0]
    i = idx[1]

    if NTask > 1:
        # send to everybody
        xi = comm.bcast(x[i], root=p)

    else:
        xi = x[i]

    return xi


def mpi_histogram(x, bins):
    """
    Return an histogram of vector x binned using binx.
    """

    # histogram
    n = np.searchsorted(np.sort(x), bins)
    n = np.concatenate([n, [len(x)]])
    hx = n[1:] - n[:-1]

    if NTask > 1:
        hx = comm.allreduce(hx, op=MPI.SUM)

    return hx


#####################################
#
# exchange function
#
#####################################


#################################
def mpi_find_a_toTask(begTask, fromTask, ex_table, delta_n):
    #################################
    """
    This function is used to find recursively an exange table
    """
    for toTask in range(begTask, NTask):
        if delta_n[toTask] > 0:		# find a node who accept particles

            if delta_n[toTask] + delta_n[fromTask] >= 0:  # can give all
                delta = -delta_n[fromTask]
            else:						# can give only a fiew
                delta = +delta_n[toTask]

            ex_table[fromTask, toTask] = +delta
            ex_table[toTask, fromTask] = -delta

            delta_n[fromTask] = delta_n[fromTask] + delta
            delta_n[toTask] = delta_n[toTask] - delta

            if delta_n[fromTask] == 0:  # everything has been distributed
                return ex_table
            else:
                return mpi_find_a_toTask(
                    begTask + 1, fromTask, ex_table, delta_n)


#################################
def mpi_GetExchangeTable(n_i):
    #################################
    """
    This function returns the exchange table
    """

    # n_i : initial repartition
    ntot = np.sum(n_i)
    if ntot == 0:
        return np.zeros((NTask, NTask))

    # final repartition
    n_f = np.zeros(NTask)
    for Task in range(NTask - 1, -1, -1):
        n_f[Task] = ntot / NTask + ntot % NTask * (Task == 0)

    # delta
    delta_n = n_f - n_i

    # find who gives what to who
    ex_table = np.zeros((NTask, NTask))

    for fromTask in range(NTask):
        if delta_n[fromTask] < 0:		  # the node gives particles
            ex_table = mpi_find_a_toTask(0, fromTask, ex_table, delta_n)

    return ex_table


#################################
def mpi_ExchangeFromTable(T, procs, ids, vec, num):
    #################################
    """
    Exchange an array according to a transfer array T

    T : exchange table

    procs : list of processor     (from Tree.GetExchanges())
    ids   : list of id		(from Tree.GetExchanges())

    vec   : vector to exchange
    num   : id corresponding to particles
    """

    # now, we have to send / recv
    SendPart = T[NTask - 1 - ThisTask, :]
    RecvPart = T[:, ThisTask]

    new_procs = np.array([])
    new_vec = np.array([])

    if vec.ndim == 1:
        #new_vec.shape = (0,3)
        pass
    elif vec.ndim == 2:
        new_vec.shape = (0, 3)

    # send/recv (1)
    for i in range(NTask):

        if i > ThisTask:
            # here, we send to i

            N = T[NTask - 1 - ThisTask, i]
            comm.send(N, i)

            if N > 0:
                to_procs = np.compress((procs == i), procs, axis=0)
                to_ids = np.compress((procs == i), ids, axis=0)
                to_vec = libutil.compress_from_lst(vec, num, to_ids)
                comm.send(to_vec, i)

                vec = libutil.compress_from_lst(vec, num, to_ids, reject=True)
                num = libutil.compress_from_lst(num, num, to_ids, reject=True)

        elif i < ThisTask:
            N = comm.recv(i)
            if N > 0:
                new_vec = np.concatenate((new_vec, comm.recv(i)))

    # send/recv (1)
    for i in range(NTask):

        if i < ThisTask:
            # here, we send to i

            N = T[NTask - 1 - ThisTask, i]
            comm.send(N, i)

            if N > 0:
                to_procs = np.compress((procs == i), procs, axis=0)
                to_ids = np.compress((procs == i), ids, axis=0)
                to_vec = libutil.compress_from_lst(vec, num, to_ids)
                comm.send(to_vec, i)

                vec = libutil.compress_from_lst(vec, num, to_ids, reject=True)
                num = libutil.compress_from_lst(num, num, to_ids, reject=True)

        elif i > ThisTask:
            N = comm.recv(i)
            if N > 0:
                new_vec = np.concatenate((new_vec, comm.recv(i)))

    # check
    c = (new_procs != ThisTask).astype(int)
    if np.sum(c) > 0:
        print("here we are in trouble")
        sys.exit()

    return np.concatenate((vec, new_vec))

    # !!!!!!!!!!!!!!!!!!!!!!! this has to be changed ....


#####################################
#
# io functions
#
#####################################


#################################
def mpi_ReadAndSendBlock(
        f,
        data_type,
        shape=None,
        byteorder=sys.byteorder,
        split=None,
        htype=np.int32):
    #################################
    """

    Read and broadcast a binary block.

    data_type = int,float32,float
    or
    data_type = array

    shape     = tuple
    """

    #####################
    # read first header
    #####################
    if ThisTask == 0:

        try:
            nb1 = np.frombuffer(f.read(4), htype)
            if sys.byteorder != byteorder:
                nb1.byteswap(True)
            nb1 = nb1[0]

        except IndexError:
            raise Exception("ReadBlockError")

    #####################
    # read a tuple
    #####################
    if isinstance(data_type, tuple):

        if ThisTask == 0:

            data = []
            for tpe in data_type:

                if isinstance(tpe, int):
                    val = f.read(tpe)
                else:
                    bytes = np.dtype(tpe).itemsize
                    val = np.frombuffer(f.read(bytes), tpe)
                    if sys.byteorder != byteorder:
                        val.byteswap(True)

                    val = val[0]

                data.append(val)

        # send the data
        if NTask > 1:

            if ThisTask == 0:
                for Task in range(1, NTask):
                    comm.send(data, dest=Task)

            else:
                data = comm.recv(source=0)

    #####################
    # read an array
    #####################
    else:

        if split:
            if ThisTask == 0:

                bytes_per_elt = data_type.bytes

                if shape is not None:
                    ndim = shape[1]
                else:
                    ndim = 1

                nelt = nb1 / bytes_per_elt / ndim
                nleft = nelt

                nread = nelt / NTask

                for Task in range(NTask - 1, -1, -1):

                    if nleft < 2 * nread and nleft > nread:
                        nread = nleft

                    nleft = nleft - nread
                    data = f.read(nread * bytes_per_elt * ndim)
                    shape = (nread, ndim)

                    if Task == ThisTask:			# this should be last
                        data = np.frombuffer(data, data_type)
                        if sys.byteorder != byteorder:
                            data.byteswap(True)
                        data.shape = shape
                    else:
                        comm.send(data, dest=Task)
                        comm.send(shape, dest=Task)

            else:
                data = comm.recv(source=0)
                shape = comm.recv(source=0)
                data = np.frombuffer(data, data_type)

                if sys.byteorder != byteorder:
                    data.byteswap(True)

                data.shape = shape

        else:

            if ThisTask == 0:

                data = np.frombuffer(f.read(nb1), data_type)
                if sys.byteorder != byteorder:
                    data.byteswap(True)

            # send the data
            if NTask > 1:
                if ThisTask == 0:
                    for Task in range(1, NTask):
                        comm.send(data, dest=Task)
                else:
                    data = comm.recv(source=0)

    #####################
    # read second header
    #####################
    if ThisTask == 0:
        nb2 = np.frombuffer(f.read(4), htype)
        if sys.byteorder != byteorder:
            nb2.byteswap(True)
        nb2 = nb2[0]

        if nb1 != nb2:
            raise Exception("ReadBlockError")

    # reshape if needed
    if split:
        # already done before
        pass
    else:
        if shape is not None:
            data.shape = shape

    return data

#################################


def mpi_ReadAndSendArray(
        f,
        data_type,
        shape=None,
        byteorder=sys.byteorder,
        npart=None,
        skip=False,
        htype=np.int32):
    #################################
    """
    Read and Brodcast a binary block assuming it contains an array.
    """

    oneD = False

    if shape is not None:
        if len(shape) == 1:
            shape = (shape[0], 1)
            oneD = True

        n_dim = shape[1]
        data = np.array([], data_type)
        data.shape = (0, shape[1])
        n_elts = shape[0]
    else:
        raise Exception(
            "mpi_ReadAndSendArray : var shape must be defined here.")
        #n_dim = 1
        #data = np.array([],data_type)
        #data.shape = (0,)

    nbytes_per_elt = np.dtype(data_type).itemsize * n_dim
    n_left = nbytes_per_elt * n_elts

    # check npart

    if npart is not None:
        ntype = len(npart)
    else:
        ntype = 1
        npart = np.array([n_elts])

    # this may be wrong in 64b, as nb1 is not equal to the number of bytes in block
    # if np.sum(npart,0) != n_elts:
    #  raise "We are in trouble here : np.sum(npart)=%d n_elts=%d"%(np.sum(npart,0),n_elts)

    #####################
    # read first header
    #####################
    if ThisTask == 0:

        try:
            nb1 = np.frombuffer(f.read(4), htype)
            if sys.byteorder != byteorder:
                nb1.byteswap(True)
            nb1 = nb1[0]

            # this may be wrong in 64b, as nb1 is not equal to the number of bytes in block
            # if nb1 != n_left:
            #  raise "We are in trouble here : nb1=%d n_left=%d"%(nb1,n_left)

        except IndexError:
            raise Exception("ReadBlockError")

    #####################
    # read data
    #####################

    if ThisTask == 0:

        if skip:
            nbytes = np.sum(npart) * nbytes_per_elt
            print(("  skipping %d bytes... " % (nbytes)))
            f.seek(nbytes, 1)
            data = None

        else:
            for i in range(ntype):

                n_write = libutil.get_n_per_task(npart[i], NTask)

                for Task in range(NTask - 1, -1, -1):

                    sdata = f.read(nbytes_per_elt * n_write[Task])

                    # send block for a slave
                    if Task != 0:
                        comm.send(sdata, dest=Task)
                    # keep block for the master
                    else:
                        sdata = np.frombuffer(sdata, data_type)
                        if shape is not None:
                            sdata.shape = (n_write[Task], shape[1])
                        data = np.concatenate((data, sdata))

    else:
        if skip:
            data = None
        else:
            for i in range(ntype):
                sdata = comm.recv(source=0)
                sdata = np.frombuffer(sdata, data_type)
                if shape is not None:
                    ne = len(sdata) // shape[1]
                    sdata.shape = (ne, shape[1])

                data = np.concatenate((data, sdata))

    if oneD and data is not None:
        data.shape = (data.shape[0],)

    #####################
    # read second header
    #####################
    if ThisTask == 0:
        nb2 = np.frombuffer(f.read(4), htype)
        if sys.byteorder != byteorder:
            nb2.byteswap(True)
        nb2 = nb2[0]

        if nb1 != nb2:
            raise Exception("ReadBlockError")

    return data


#################################
def mpi_GatherAndWriteArray(
        f,
        data,
        byteorder=sys.byteorder,
        npart=None,
        htype=np.int32):
    #################################
    """
    Gather and array and write it in a binary block.

    data = array

    shape     = tuple
    """

    # check npart
    if npart is not None:
        pass
    else:
        npart = np.array([len(data)])

    data_nbytes = mpi_allreduce(data.nbytes)

    if ThisTask == 0:

        nbytes = np.array([data_nbytes], htype)

        if sys.byteorder != byteorder:
            nbytes.byteswap(True)

        # write header 1
        f.write(nbytes.tostring())

    # loop over particles type

    for i in range(len(npart)):

        n_write = libutil.get_n_per_task(npart[i], NTask)

        if ThisTask == 0:

            for Task in range(NTask - 1, -1, -1):

                if Task != 0:
                    sdata = comm.recv(source=Task)
                else:
                    i1 = int(np.sum(npart[:i]))
                    i2 = int(i1 + npart[i])
                    sdata = data[i1:i2]

                if sys.byteorder != byteorder:
                    sdata.byteswap(True)

                f.write(sdata.tostring())

        else:

            i1 = int(np.sum(npart[:i]))
            i2 = int(i1 + npart[i])

            comm.send(data[i1:i2], dest=0)

    if ThisTask == 0:
        # write header 2
        f.write(nbytes.tostring())


#################################
def mpi_OldReadAndSendArray(
        f,
        data_type,
        shape=None,
        skip=None,
        byteorder=sys.byteorder,
        nlocal=None):
    #################################
    """

    Read and Brodcast a binary block assuming it contains an array.
    The array is splitted acroding to the variable nlocal.

    data_type = array type
    shape     = tuple

    nlocal : array   NTask x Npart
             array   NTask

    """

    #####################
    # read first header
    #####################
    if ThisTask == 0:

        try:
            nb1 = np.frombuffer(f.read(4), np.int32)
            if sys.byteorder != byteorder:
                nb1.byteswap(True)
            nb1 = nb1[0]

        except IndexError:
            raise Exception("ReadBlockError")

    #####################
    # read an array
    #####################

    if nlocal.ndim != 2:
        raise Exception("OldReadAndSendArray error", "nlocal must be of rank 2")
    else:
        ntype = nlocal.shape[1]

    if shape is not None:
        ndim = shape[1]
        data = np.array([], data_type)
        data.shape = (0, shape[1])
    else:
        ndim = 1
        data = np.array([], data_type)
        data.shape = (0,)

    nbytes_per_elt = data_type.itemsize * ndim

    if ThisTask == 0:

        for i in range(ntype):
            for Task in range(NTask - 1, -1, -1):
                sdata = f.read(nbytes_per_elt * int(nlocal[Task, i]))

                # send block for a slave
                if Task != 0:
                    comm.send(sdata, dest=Task)
                # keep block for the master
                else:
                    sdata = np.frombuffer(sdata, data_type)
                    if shape is not None:
                        sdata.shape = (nlocal[ThisTask, i], shape[1])
                    data = np.concatenate((data, sdata))

    else:

        for i in range(ntype):
            sdata = comm.recv(source=0)
            sdata = np.frombuffer(sdata, data_type)
            if shape is not None:
                sdata.shape = (nlocal[ThisTask, i], shape[1])

            data = np.concatenate((data, sdata))

    #####################
    # read second header
    #####################
    if ThisTask == 0:
        nb2 = np.frombuffer(f.read(4), np.int32)
        if sys.byteorder != byteorder:
            nb2.byteswap(True)
        nb2 = nb2[0]

        if nb1 != nb2:
            raise Exception("ReadBlockError")

    return data


#################################
def mpi_OldGatherAndWriteArray(f, data, byteorder=sys.byteorder, nlocal=None):
    #################################
    """
    Gather and array and write it in a binary block.

    data = array

    shape	    = tuple
    """

    if nlocal.ndim != 2:
        raise Exception("OldGatherAndWriteArray error", "nlocal must be of rank 2")
    else:
        ntype = nlocal.shape[1]

    data_size = mpi_allreduce(data.size)

    if ThisTask == 0:

        nbytes = np.array([data.dtype.itemsize * data_size], np.int32)

        if sys.byteorder != byteorder:
            nbytes.byteswap(True)

        # write header 1
        f.write(nbytes.tostring())

    # loop over particles type
    i1 = 0

    for i in range(ntype):

        if ThisTask == 0:

            for Task in range(NTask - 1, -1, -1):

                if Task != 0:
                    sdata = comm.recv(source=Task)
                else:

                    i2 = i1 + int(nlocal[Task, i])

                    sdata = data[i1:i2]
                    i1 = i2

                if sys.byteorder != byteorder:
                    sdata.byteswap(True)

                f.write(sdata.tostring())

        else:

            i2 = i1 + int(nlocal[ThisTask, i])

            comm.send(data[i1:i2], dest=0)
            i1 = i2

    if ThisTask == 0:
        # write header 2
        f.write(nbytes.tostring())
