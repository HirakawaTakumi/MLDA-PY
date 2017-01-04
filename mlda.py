# encoding: shift_jis
import numpy
import random
import math
import pylab
import pickle
import os

# �n�C�p�[�p�����[�^
__alpha = 1.0
__beta = 1.0

def plot( n_dz, liks, D, K ):
    print "�ΐ��ޓx�F", liks[-1]
    doc_dopics = numpy.argmax( n_dz , 1 )
    print "���ތ��ʁF", doc_dopics
    print "---------------------"


    # �O���t�\��
    pylab.clf()
    pylab.subplot("121")
    pylab.title( "P(z|d)" )
    pylab.imshow( n_dz / numpy.tile(numpy.sum(n_dz,1).reshape(D,1),(1,K)) , interpolation="none" )
    pylab.subplot("122")
    pylab.title( "liklihood" )
    pylab.plot( range(len(liks)) , liks )
    pylab.draw()
    pylab.pause(0.1)

def calc_lda_param( docs_mdn, topics_mdn, K, dims ):
    M = len(docs_mdn)
    D = len(docs_mdn[0])

    # �e����d�ɂ����ăg�s�b�Nz������������
    n_dz = numpy.zeros((D,K))

    # �e�g�s�b�Nz�ɂ҂����ē���w������������
    n_mzw = [ numpy.zeros((K,dims[m])) for m in range(M)]

    # �e�g�s�b�N������������
    n_mz = [ numpy.zeros(K) for m in range(M) ]

    # �����グ��
    for d in range(D):
        for m in range(M):
            if dims[m]==0:
                continue
            N = len(docs_mdn[m][d])    # ���̂Ɋ܂܂�������
            for n in range(N):
                w = docs_mdn[m][d][n]       # ����d��n�Ԗڂ̓����̃C���f�b�N�X
                z = topics_mdn[m][d][n]     # �����Ɋ��蓖�Ă��Ă���g�s�b�N
                n_dz[d][z] += 1
                n_mzw[m][z][w] += 1
                n_mz[m][z] += 1

    return n_dz, n_mzw, n_mz


def sample_topic( d, w, n_dz, n_zw, n_z, K, V ):
    P = [ 0.0 ] * K

    # �ݐϊm�����v�Z
    P = (n_dz[d,:] + __alpha )*(n_zw[:,w] + __beta) / (n_z[:] + V *__beta)
    for z in range(1,K):
        P[z] = P[z] + P[z-1]

    # �T���v�����O
    rnd = P[K-1] * random.random()
    for z in range(K):
        if P[z] >= rnd:
            return z



# �P������ɕ��ׂ����X�g�ϊ�
def conv_to_word_list( data ):
    V = len(data)
    doc = []
    for v in range(V):  # v:��b�̃C���f�b�N�X
        for n in range(data[v]): # ��b�̔��������񐔕�for����
            doc.append(v)
    return doc

# �ޓx�v�Z
def calc_liklihood( data, n_dz, n_zw, n_z, K, V  ):
    lik = 0

    P_wz = (n_zw.T + __beta) / (n_z + V *__beta)
    for d in range(len(data)):
        Pz = (n_dz[d] + __alpha )/( numpy.sum(n_dz[d]) + K *__alpha )
        Pwz = Pz * P_wz
        Pw = numpy.sum( Pwz , 1 ) + 0.000001
        lik += numpy.sum( data[d] * numpy.log(Pw) )

    return lik

def save_model( save_dir, n_dz, n_mzw, n_mz, M, dims ):
    try:
        os.mkdir( save_dir )
    except:
        pass

    Pdz = n_dz + __alpha
    Pdz = (Pdz.T / Pdz.sum(1)).T
    numpy.savetxt( os.path.join( save_dir, "Pdz.txt" ), Pdz, fmt=str("%f") )

    for m in range(M):
        Pwz = (n_mzw[m].T + __beta) / (n_mz[m] + dims[m] *__beta)
        Pdw = Pdz.dot(Pwz.T)
        numpy.savetxt( os.path.join( save_dir, "Pmdw[%d].txt" % m ) , Pdw )

    with open( os.path.join( save_dir, "model.pickle" ), "wb" ) as f:
        pickle.dump( [n_mzw, n_mz], f )


def load_model( load_dir ):
    model_path = os.path.join( load_dir, "model.pickle" )
    with open(model_path, "rb" ) as f:
        a,b = pickle.load( f )

    return a,b

# lda���C��
def mlda( data, K, num_itr=100, save_dir="model", load_dir=None ):
    pylab.ion()

    # �ޓx�̃��X�g
    liks = []

    M = len(data)       # ���_���e�B��

    dims = []
    for m in range(M):
        if data[m] is not None:
            dims.append( len(data[m][0]) )
            D = len(data[m])    # ���̐�
        else:
            dims.append( 0 )

    # data���̒P������ɕ��ׂ�i�v�Z���₷�����邽�߁j
    docs_mdn = [[ None for i in range(D) ] for m in range(M)]
    topics_mdn = [[ None for i in range(D) ] for m in range(M)]
    for d in range(D):
         for m in range(M):
            if data[m] is not None:
                docs_mdn[m][d] = conv_to_word_list( data[m][d] )
                topics_mdn[m][d] = numpy.random.randint( 0, K, len(docs_mdn[m][d]) ) # �e�P��Ƀ����_���Ńg�s�b�N�����蓖�Ă�

    # LDA�̃p�����[�^���v�Z
    n_dz, n_mzw, n_mz = calc_lda_param( docs_mdn, topics_mdn, K, dims )

    # �F�����[�h�̎��͊w�K�����p�����[�^��ǂݍ���
    if load_dir:
        n_mzw, n_mz = load_model( load_dir )

    for it in range(num_itr):
        # ���C���̏���
        for d in range(D):
            for m in range(M):
                if data[m] is None:
                    continue

                N = len(docs_mdn[m][d]) # ����d�̃��_���e�Bm�Ɋ܂܂�������
                for n in range(N):
                    w = docs_mdn[m][d][n]       # �����̃C���f�b�N�X
                    z = topics_mdn[m][d][n]     # �����Ɋ��蓖�Ă��Ă���J�e�S��


                    # �f�[�^����菜���p�����[�^���X�V
                    n_dz[d][z] -= 1

                    if not load_dir:
                        n_mzw[m][z][w] -= 1
                        n_mz[m][z] -= 1

                    # �T���v�����O
                    z = sample_topic( d, w, n_dz, n_mzw[m], n_mz[m], K, dims[m] )

                    # �f�[�^���T���v�����O���ꂽ�N���X�ɒǉ����ăp�����[�^���X�V
                    topics_mdn[m][d][n] = z
                    n_dz[d][z] += 1

                    if not load_dir:
                        n_mzw[m][z][w] += 1
                        n_mz[m][z] += 1

        lik = 0
        for m in range(M):
            if data[m] is not None:
                lik += calc_liklihood( data[m], n_dz, n_mzw[m], n_mz[m], K, dims[m] )
        liks.append( lik )
        plot( n_dz, liks, D, K )

    save_model( save_dir, n_dz, n_mzw, n_mz, M, dims )

    pylab.ioff()
    pylab.show()

def main():
    data = []
    data.append( numpy.loadtxt( "histogram_v.txt" , dtype=numpy.int32) )
    data.append( numpy.loadtxt( "histogram_w.txt" , dtype=numpy.int32)*5 )
    mlda( data, 3, 100, "learn_result" )

    data[1] = None
    mlda( data, 3, 10, "recog_result" , "learn_result" )


if __name__ == '__main__':
    main()

