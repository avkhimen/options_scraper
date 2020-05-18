import argparse

def get_input_args():
    """Returns input arguments for main file execution"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--market', type = str, default = 'NYSE', 
                        help = 'Market to get stocks from')
    parser.add_argument('--discount_threshold', type = float, default = 0.025, 
                        help = 'Allowable spread ask/(ask + strike) for filtering options')
    parser.add_argument('--strategy', type = str, default = 'options', 
                        help = 'Strategy to execute')
    return parser.parse_args()