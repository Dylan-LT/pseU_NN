from torch_geometric.nn.dense import DenseGraphConv
from torch.nn import Dropout
import torch
import torch.nn as nn
import math

class PositionalEncoding(nn.Module):

    def __init__(self, d_model, dropout=0.1, max_len=5000):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        self.register_buffer('pe', pe)

    def forward(self, x):
        x = x + self.pe[:x.size(0), :]
        return self.dropout(x)


class DenseGraphEncoder(nn.Module):
    def __init__(self, output_dim,num_nodes):
        super().__init__()
        self.graph_conv1 = DenseGraphConv(4 + num_nodes, 128, aggr='add') 
        self.act1 = nn.ReLU()
        self.norm1 = nn.Sequential(
            Permute(),
            nn.BatchNorm1d(128),
            Permute()
        )
        self.dropout1 = Dropout(0.2)
        self.graph_conv2 = DenseGraphConv(128, output_dim, aggr='add')

    def forward(self, x, adj):
        x = self.graph_conv1(x, adj)
        x = self.act1(x)
        x = self.norm1(x)
        x = self.dropout1(x)
        x = self.graph_conv2(x, adj)
        return x



class Permute(nn.Module):
    def __init__(self):
        super().__init__()

    def forward(self, x):
        return x.permute(0, 2, 1)


class transformer_GNN(nn.Module):
    def __init__(self, num_nodes, hidden_dim=32):
        super().__init__()
        self.w1 = nn.Parameter(torch.tensor(0.5))

        gnn_output_dim = 64
        self.gnn_encoder = DenseGraphEncoder(gnn_output_dim,num_nodes)

        self.fc_cnn = nn.Sequential(
            nn.Linear(gnn_output_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2)
        )
        # CNN-based positional encoder
        self.conv = nn.Sequential(
            nn.Conv1d(in_channels=4, out_channels=128, kernel_size=5, padding=2),  # 更宽 receptive field
            nn.BatchNorm1d(128),
            nn.ReLU(inplace=True),
            nn.Conv1d(in_channels=128, out_channels=32, kernel_size=3, padding=1),
            nn.BatchNorm1d(32),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2)
        )
        self.lstm = nn.LSTM(input_size=hidden_dim, hidden_size=hidden_dim//2, num_layers=2, batch_first=True, dropout=0.25, bidirectional=True)
        self.pos_embedding_dim = PositionalEncoding(d_model=hidden_dim, dropout=0, max_len=num_nodes)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim,
            dim_feedforward=128,
            nhead=8,
            dropout=0.25,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=1)
        # final output layer
        self.final_fc = nn.Sequential(
            nn.ReLU(),
            nn.BatchNorm1d(32 + 32),
            nn.Linear(32 + 32, 32), 
            nn.Dropout(0.2),
            nn.Linear(32,1), 
            nn.Sigmoid()
        )
        
        self.num_nodes = num_nodes
        
    def forward(self, batch):
        x = batch.x
        adj = x[:, :, :self.num_nodes]
        seq = x[:, :, self.num_nodes:]
        
        # adj feature
        adj_x = self.gnn_encoder(torch.cat([adj, seq], dim=2), adj)
        adj_x = self.fc_cnn(adj_x)
        adj_x = torch.mean(adj_x, dim=1)
       

        # sequence feature
        seq_x= seq.permute(0, 2, 1)
        seq_x = self.conv(seq_x)
        seq_x= seq_x.permute(0, 2, 1)
        seq_x_lstm, _ = self.lstm(seq_x)
        seq_x = self.pos_embedding_dim(seq_x_lstm+seq_x)
        seq_x = self.transformer(seq_x)
        seq_x = torch.mean(seq_x, dim=1)
        fused = torch.cat((adj_x , seq_x),dim=1)
        fused= self.final_fc(fused)
        return fused
    