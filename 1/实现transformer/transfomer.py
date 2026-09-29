from typing import Any

import torch
import torch.nn as nn
import math

from openai.types import batch
from torch.nn.modules import dropout


class PositionalEncoding(nn.Module):
    """
    位置编码模块
    """
    def forward(self,x):


class MultiHeadAttention(nn.Module):
    """
    多头注意力机制模块
    """
    def forward(self,d_model,num_heads):
        super(MultiHeadAttention,self).__init__()
        assert  d_model % num_heads == 0,"d_model必须能被num_heads整除"

        self.d_model=d_model
        self.num_heads=num_heads
        self.d_k = d_model/num_heads

        #定义QKV和输出线性变换层
        self.W_q = nn.Linear(d_model,d_model)
        self.W_k = nn.Linear(d_model,d_model)
        self.W_v = nn.Linear(d_model,d_model)
        self.W_o = nn.Linear(d_model,d_model)

    def scaled_dot_attention(self,Q,K,V,mask=None):
        #1.计算注意力得分
        attn_scores = torch.matmul(Q,K.transpose(-2,-1))/math.sqrt(self._model)

        #2.应用掩码(如果提供)
        if mask is not None:
            attn_scores = attn_scores.masked_fill(mask==0,-1e9)

        #3.注意力权重计算
        attn_probs = torch.softmax(attn_scores,dim=-1)

        #4.加权求和
        output = torch.matmul(attn_probs,V)
        return output

    def split_heads(self,x):
        #将输入的x的形状从(batch_size,seq_length,d_model)
        #变成(batch_size,num_heads,seq_length,d_k)
        batch_size,seq_length,d_model = x.size()
        return x.view(batch_size,seq_length,self.num_heads,self.d_k).transpose(1,2)

    def combine_heads(self,x):
        #将输入x的形状变回去
        batch_size,num_head,seq_length,d_k=x.size()
        return x.transpose(1,2).contiguous().view(batch_size,seq_length,self.d_model)

    def forward(self,Q,K,V,mask=None):
        #1.对QKV进行线性变换
        Q = self.split_heads(self.W_q(Q))
        K = self.split_heads(self.W_k(K))
        V = self.split_heads(self.W_v(V))

        #2.计算注意力分数
        attn_output = self.scaled_dot_attention(Q,K,V,mask)

        #3.合并多头
        output= self.W_o(self.combine_heads(attn_output))
        return output


class PositionWiseFeedForward(nn.Module):
    """
    位置前馈网络模块
    """
    def __init__(self, d_model, d_ff, dropout=0.1):
        super(PositionWiseFeedForward,self).__init__()
        self.linear1 = nn.Linear(d_model,d_ff)
        self.dropout = nn.Dropout(dropout)
        self.linear2 = nn.Linear(d_ff,d_model)
        self.relu = nn.ReLU()

    def forward(self,x):
        x=self.linear1(x)
        x=self.relu(x)
        x=self.dropout(x)
        x=self.linear2(x)
        return x

#编码器核心层
class EncoderLayer(nn.Module):
    def __init__(self,d_model,num_heads,d_ff,dropout):
        super(EncoderLayer,self).__init__()
        self.self_attn=MultiHeadAttention()
        self.feed_forward = PositionWiseFeedForward()
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)
    def forward(self,x,mask):
        #残差连接与层归一化
        #1.多头自注意力
        attn_output = self.self_attn(x,x,x,mask)
        x = self.norm1(x+self.dropout(attn_output))

        #2.前馈网络
        ff_output = self.feed_forward(x)
        x = self.norm2(x+self.dropout(ff_output))

        return x

#---解码器核心层---

class DecoderLayer(nn.Module):
    def __init__(self, d_model,num_heads,d_ff,dropout):
        super(DecoderLayer,self).__init__()
        self.self_attn = MultiHeadAttention() #待实现
        self.cross_attn = MultiHeadAttention()
        self.feed_forward = PositionWiseFeedForward()
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.norm3 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self,x,encoder_output,src_mask,tgt_mask):
        #1.掩码多头自注意力
        attn_output = self.self_attn(x,x,x,tgt_mask)
        x = self.norm1(x+self.dropout(attn_output))

        #2.交叉注意力
        cross_attn_output = self.cross_attn(x,encoder_output,encoder_output,src_mask)
        x = self.norm2(x+self.dropout(cross_attn_output))

        #3.前馈网络
        ff_output = self.feed_forward(x)
        x = self.norm3(x+self.dropout(ff_output))

        return x


