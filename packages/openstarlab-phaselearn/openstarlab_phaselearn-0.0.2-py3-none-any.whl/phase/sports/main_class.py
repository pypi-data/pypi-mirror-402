from .soccer.main_class_soccer.main import phase_model_soccer

class Phase_Model:
    soccer_phase_model = ['transformer', 'baller2vec', 'gcn_transformer', 'gat_transformer']
    other_model = []

    def __new__(cls, model_name, team_mode):
        if model_name in cls.soccer_phase_model:
            return phase_model_soccer(model_name, team_mode)
        elif model_name in cls.other_model:
            raise NotImplementedError('other model not implemented yet')
        else:
            raise ValueError(f'Unknown event model: {model_name}')


def main():
    import os
    import argparse
    args = argparse.ArgumentParser()
    args.add_argument('--mode', required=True, choices=['train', 'quantitative_test', 'qualitative_analysis', 'live_prediction'], help='')
    args.add_argument('--model', required=True, choices=['transformer', 'baller2vec', 'gcn_transformer', 'gat_transformer'], help='kind of model')
    args.add_argument('--team_mode', required=False, choices=['1team_mode', '2team_mode'], help='number of team to predict play phase')
    args = args.parse_args()
    mode = args.mode
    model_name = args.model
    team_mode = args.team_mode
    if model_name == 'baller2vec':
        train_date = '20251221_150156' 
    elif model_name == 'transformer':
        train_date = '20251221_153159'
    elif model_name == 'gcn_transformer':
        train_date = '20251221_155119'
    elif model_name == 'gat_transformer':
        if team_mode == '1team_mode':
            train_date = '20260110_191939'
        else:
            train_date = '20260111_041317'
    model = Phase_Model(model_name=model_name, team_mode=team_mode)
    if mode == 'train':
        train_config = f'phase/sports/soccer/models/model_yaml/train_{model_name}.yaml'
        model.train(train_config)
    elif mode == 'quantitative_test':
        model_config = os.getcwd()+f'/model/{model_name}/{team_mode}/{train_date}/run_1/hyperparameters.json'
        model.quantitative_test(model_config)
    elif mode == 'qualitative_analysis':
        model_config = os.getcwd()+f'/model/{model_name}/{team_mode}/{train_date}/run_1/hyperparameters.json'
        qualitative_analysis_sequence_np_path = 'data/inference_data/bepro/117093/117093_09_22-10_07_sequence_np.npy'
        qualitative_analysis_label_np_path = 'data/inference_data/bepro/117093/117093_09_22-10_07_label_np.npy'
        qualitative_analysis_time_np_path = 'data/inference_data/bepro/117093/117093_09_22-10_07_time_np.npy'
        qualitative_analysis_phase_data_path = 'data/phase_data/bepro/117093/117093_main_data.csv'
        qualitative_analysis_phase_annotation_data_path = 'data/phase_annotation_data/bepro/117093/117093_09_22-10_07_annotation.csv'
        model.qualitative_analysis(model_config, sequence_np_path=qualitative_analysis_sequence_np_path, label_np_path=qualitative_analysis_label_np_path, 
                    time_np_path=qualitative_analysis_time_np_path, phase_data_path=qualitative_analysis_phase_data_path, phase_annotation_data_path=qualitative_analysis_phase_annotation_data_path)
    elif mode == 'live_prediction':
        model_config = os.getcwd()+f'/model/{model_name}/{team_mode}/{train_date}/run_1/hyperparameters.json'
        live_prediction_sequence_np_path = 'data/inference_data/bepro/117092/117092_sequence_np.npy'
        live_prediction_time_np_path = 'data/inference_data/bepro/117092/117092_time_np.npy'
        live_prediction_phase_data_path = 'data/phase_data/bepro/117092/117092_main_data.csv'
        model.live_prediction(model_config, sequence_np_path=live_prediction_sequence_np_path, time_np_path=live_prediction_time_np_path, phase_data_path=live_prediction_phase_data_path)
    print('Done')


if __name__ == '__main__':
    main()