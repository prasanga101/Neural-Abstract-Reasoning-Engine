#This implementation will not be using in the Project and is just added for understanding purposes
'''
There is a tsunami in India
"India" Location matters
"There is" comparatively less useful
for each word, decide which other words are important to it
Q = What am I looking for?
K = What do I offer?
V = What Information do I carry?
'''
import torch
import torch.nn as nn
import math

class SelfAttention(nn.Module):
    def __init__(self , d_model):
        super().__init__()
        self.W_q = nn.Linear(d_model , d_model) # makes query for each token
        self.W_k = nn.Linear(d_model , d_model) #makes key for every token
        self.W_v = nn.Linear(d_model , d_model) #makes value for each token

    def forward(self , x , mask = None):
        Q = self.W_q(x)
        K = self.W_k(x)
        V = self.W_v(x)
        # scores check which sentense should care about whom
        #mask ensures that token cannot see the future eg token 1 cant see token 2 and 3 ; 
        # token 2 can see token 1 , 2 but not token 3
        #dimension for matrix multiplication is done here

        scores = Q @ K.transpose(-2,-1)
        scores = scores/math.sqrt(x.size(-1)) #dim -1 means the last dimension of x that is the d_model
        if mask is not None:
            scores = scores.masked_fill(mask == 0 , -1e9)
        #turns the sentences into the attention weights
        #converts the weight into probablilities the sum of them is 1
        #creates attention distribution
        #dim = -1 to apply softmax across tokens
        weights = torch.softmax(scores , dim = -1)
        #Final smarter tojen reporesentation
        output = torch.matmul(weights , V)


        return output,weights