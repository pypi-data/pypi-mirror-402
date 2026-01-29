import yaml
import json
import os
import numpy as np

from ..utils.load_train_data import load_train_data, load_qualitative_analysis_data, load_live_prediction_data
from ..utils.preprocessing import preprocessing_data
from ..utils.augmentation import augmentation

from ..models.transformer import train_main as transformer_train_main
from ..models.transformer import inference_main as transformer_inference_main
from ..models.baller2vec import train_main as baller2vec_train_main
from ..models.baller2vec import inference_main as baller2vec_inference_main
from ..models.gcn_transformer import train_main as gcn_transformer_train_main
from ..models.gcn_transformer import inference_main as gcn_transformer_inference_main
from ..models.gat_transformer import train_main as gat_transformer_train_main
from ..models.gat_transformer import inference_main as gat_transformer_inference_main

from ..utils.evaluation import quantitative_test, generate_sequence_result

class phase_model_soccer:
    def __init__(self, model_name, team_mode):
        self.model_name = model_name
        self.team_mode = team_mode

    def train(self, train_config):
        with open(train_config, 'r') as file:
            train_config = yaml.safe_load(file)

        data_config = train_config.get('data', {})
        sequence_np_path = data_config.get('train_sequence_np_path')
        label_np_path = data_config.get('train_label_np_path')
        augmentation_bool = data_config.get('augmentation')

        if sequence_np_path and label_np_path and os.path.exists(sequence_np_path) and os.path.exists(label_np_path):
            sequence_np = np.load(sequence_np_path)
            label_np = np.load(label_np_path)
        else:
            all_match_tracking_data, all_match_annotation_data = load_train_data()
            sequence_np, label_np, _ = preprocessing_data(all_match_tracking_data, sequence_np_path, all_match_annotation_data, label_np_path)
            if augmentation_bool:
                sequence_np, label_np = augmentation(sequence_np, label_np, self.team_mode)
            elif self.team_mode == '1team_mode':
                label_np = label_np[:9]
            np.save(sequence_np_path, sequence_np)
            np.save(label_np_path, label_np)
            print(f" saved sequence_np shape: {sequence_np.shape} and label_np shape: {label_np.shape}")

        if self.model_name == 'transformer':
            transformer_train_main(sequence_np, label_np, train_config)
        elif self.model_name == 'baller2vec':
            baller2vec_train_main(sequence_np, label_np, train_config)
        elif self.model_name == 'gcn_transformer':
            gcn_transformer_train_main(sequence_np, label_np, train_config)
        elif self.model_name == 'gat_transformer':
            gat_transformer_train_main(sequence_np, label_np, train_config)
        else:
            raise ValueError(f'Unknown model name: {self.model_name}')
    
    def quantitative_test(self, model_config):
        with open(model_config, 'r', encoding='utf-8') as f:
            model_config = json.load(f)

        sequence_np_path = model_config.get('train_sequence_np_path')
        label_np_path = model_config.get('train_label_np_path')
        sequence_np = np.load(sequence_np_path)
        label_np = np.load(label_np_path)
        if self.team_mode == '1team_mode':
            label_np = label_np[:9]

        if self.model_name == 'transformer':
            outputs_np, labels_np = transformer_inference_main(sequence_np, label_np, model_config, inference_type='quantitative_test')
        elif self.model_name == 'baller2vec':
            outputs_np, labels_np = baller2vec_inference_main(sequence_np, label_np, model_config, inference_type='quantitative_test')
        elif self.model_name == 'gcn_transformer':
            outputs_np, labels_np = gcn_transformer_inference_main(sequence_np, label_np, model_config, inference_type='quantitative_test')
        elif self.model_name == 'gat_transformer':
            outputs_np, labels_np = gat_transformer_inference_main(sequence_np, label_np, model_config, inference_type='quantitative_test')
        else:
            raise ValueError(f'Unknown model name: {self.model_name}')
        
        save_path = model_config['save_dir']+f"/data/evaluation/{model_config['model_name']}/{model_config['train_mode']}/{model_config['current_time']}/run_{model_config['run']}/"
        if not os.path.exists(save_path):
            os.makedirs(save_path, exist_ok=True)
        regression_df, top_k_df, classification_df = quantitative_test(outputs_np, labels_np, team_mode=self.team_mode)
        regression_df.to_csv(f'{save_path}/regression.csv', index=False)
        top_k_df.to_csv(f'{save_path}/top_k.csv', index=False)
        classification_df.to_csv(f'{save_path}/classification.csv', index=False)
    
    def qualitative_analysis(self, model_config, sequence_np_path=None, label_np_path=None, time_np_path=None, phase_data_path=None, phase_annotation_data_path=None):
        with open(model_config, 'r', encoding='utf-8') as f:
            model_config = json.load(f)

        if sequence_np_path and label_np_path and os.path.exists(sequence_np_path) and os.path.exists(label_np_path):
            sequence_np = np.load(sequence_np_path)
            label_np = np.load(label_np_path)
            time_np = np.load(time_np_path)
        else:
            all_match_tracking_data, all_match_annotation_data = load_qualitative_analysis_data(phase_data_path, phase_annotation_data_path)
            sequence_np, label_np, time_np = preprocessing_data(all_match_tracking_data, sequence_np_path, all_match_annotation_data, label_np_path, time_np_path)
        if self.team_mode == '1team_mode':
            label_np = label_np[:9]

        if self.model_name == 'transformer':
            outputs_np, labels_np = transformer_inference_main(sequence_np, label_np, model_config, inference_type='qualitative_analysis')
        elif self.model_name == 'baller2vec':
            outputs_np, labels_np = baller2vec_inference_main(sequence_np, label_np, model_config, inference_type='qualitative_analysis')
        elif self.model_name == 'gcn_transformer':
            outputs_np, labels_np = gcn_transformer_inference_main(sequence_np, label_np, model_config, inference_type='qualitative_analysis')
        elif self.model_name == 'gat_transformer':
            outputs_np, labels_np = gat_transformer_inference_main(sequence_np, label_np, model_config, inference_type='qualitative_analysis')
        else:
            raise ValueError(f'Unknown model name: {self.model_name}')
        
        save_path = model_config['save_dir']+f"/data/evaluation/{model_config['model_name']}/{model_config['train_mode']}/{model_config['current_time']}/run_{model_config['run']}/"
        if not os.path.exists(save_path):
            os.makedirs(save_path, exist_ok=True)
        result_df = generate_sequence_result(time_np, outputs_np, labels_np, inference_type='qualitative_analysis', team_mode=self.team_mode)
        result_df.to_csv(f'{save_path}/qualitative_analysis.csv', index=False)
    
    def live_prediction(self, model_config, sequence_np_path=None, time_np_path=None, phase_data_path=None):
        with open(model_config, 'r', encoding='utf-8') as f:
            model_config = json.load(f)

        if sequence_np_path and time_np_path and os.path.exists(sequence_np_path) and os.path.exists(time_np_path):
            sequence_np = np.load(sequence_np_path)
            time_np = np.load(time_np_path)
        else:
            all_match_tracking_data = load_live_prediction_data(phase_data_path)
            sequence_np, time_np = preprocessing_data(all_match_tracking_data, sequence_np_path, time_np_path=time_np_path)
        label_np = np.zeros((sequence_np.shape[0], 1), dtype=np.float32)

        if self.model_name == 'transformer':
            outputs_np, labels_np = transformer_inference_main(sequence_np, label_np, model_config, inference_type='live_prediction')
        elif self.model_name == 'baller2vec':
            outputs_np, labels_np = baller2vec_inference_main(sequence_np, label_np, model_config, inference_type='live_prediction')
        elif self.model_name == 'gcn_transformer':
            outputs_np, labels_np = gcn_transformer_inference_main(sequence_np, label_np, model_config, inference_type='live_prediction')
        elif self.model_name == 'gat_transformer':
            outputs_np, labels_np = gat_transformer_inference_main(sequence_np, label_np, model_config, inference_type='live_prediction')
        else:
            raise ValueError(f'Unknown model name: {self.model_name}')
        
        save_path = model_config['save_dir']+f"/data/evaluation/{model_config['model_name']}/{model_config['train_mode']}/{model_config['current_time']}/run_{model_config['run']}/"
        if not os.path.exists(save_path):
            os.makedirs(save_path, exist_ok=True)
        result_df = generate_sequence_result(time_np, outputs_np, labels_np, inference_type='live_prediction', team_mode=self.team_mode)
        result_df.to_csv(f'{save_path}/live_prediction.csv', index=False)