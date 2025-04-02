from torch_geometric.nn.dense import DenseGraphConv
from torch.nn import Dropout
from torch.nn import functional as F
from tqdm.auto import tqdm
import torch
import torch.nn as nn

BASES = ['A', 'U', 'C', 'G']
BASE_TO_INDEX = {base: idx for idx, base in enumerate(BASES)}
SEQUENCE_LENGTH = 61
num_nodes = SEQUENCE_LENGTH
class DenseGraphEncoder(nn.Module):
    def __init__(self, output_dim):
        super(DenseGraphEncoder, self).__init__()
        self.graph_conv1 = DenseGraphConv(len(BASES) + num_nodes, 128, aggr='add') 
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
        super(Permute, self).__init__()

    def forward(self, x):
        return x.permute(0, 2, 1)


class transformer_GNN(nn.Module):
    def __init__(self, num_nodes, hidden_dim=64):
        super(transformer_GNN, self).__init__()
        self.w1 = nn.Parameter(torch.tensor(0.5))

        gnn_output_dim = 64
        self.gnn_encoder = DenseGraphEncoder(gnn_output_dim)

        self.fc_cnn = nn.Sequential(
            nn.Linear(gnn_output_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
        )

        self.pos_encoder = nn.Sequential(
            nn.Linear(4, 32)
        )

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=32,
            dim_feedforward=256,
            nhead=4,
            dropout=0.25,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=4)
        self.simplecat=nn.Linear(32,64)
        # final output layer
        self.final_fc = nn.Sequential(
            nn.ReLU(),
            nn.BatchNorm1d(32 + 32),
            nn.Linear(32 + 32, 32),  
            nn.ReLU(),
            nn.BatchNorm1d(32),
            nn.Dropout(0.3),
            nn.Linear(32,1),
            nn.Sigmoid()
        )
        
        self.num_nodes = num_nodes
        
    def forward(self, batch, batch_size):
        x = batch.x
        adj = x[:, :, :self.num_nodes]
        x = x[:, :, self.num_nodes:]
        
        # adj feature
        adj_x = self.gnn_encoder(torch.cat([adj, x], dim=2), adj)
        adj_x = F.relu(adj_x)
        adj_x = torch.mean(adj_x, dim=1)
        adj_x = adj_x.view(batch_size, -1)
        adj_x = self.fc_cnn(adj_x)

        # sequence feature
        seq_x = self.pos_encoder(x)
        seq_x = F.relu(self.transformer(seq_x))
        #seq_x =  seq_x.mean(dim=1) # Global average pooling
        seq_x = torch.mean(seq_x, dim=1)
        #seq_x = self.dropout(seq_x)
        # feature fusion
        #x = torch.cat((adj_x, seq_x), dim=1)
        # Weighted sum fusion
        fused = self.weighted_sum_fusion(adj_x, seq_x)
        fused= self.final_fc(fused)
        return fused
    def weighted_sum_fusion(self, adj_x, seq_x):  
        fused = torch.cat((self.w1*adj_x ,(1-self.w1) * seq_x),dim=1)
        return fused 
