function result = matlab_interface(input_value, python_cmd)
% MATLAB_INTERFACE MATLAB interface entry point for the fpga_interface project.
%
% Responsibilities:
%   - Provide a clean MATLAB-side interface for sending values through the CLI.
%   - Receive values returned from the CLI.
%   - Keep MATLAB processing separate from communication logic.
%
% Flow:
%   MATLAB -> encode_for_cli -> CLI -> Python encoder -> Verilog -> Python decoder -> CLI -> decode_from_cli -> MATLAB
%
% Example:
%   result = matlab_interface(25);
%   disp(result); % Displays 25

    if nargin < 2 || isempty(python_cmd)
        python_cmd = 'python';
    end

    if nargin < 1
        input_value = 25; % Default Iteration 1 test value
    end

    % 1. Encode MATLAB numerical value for CLI protocol
    cli_arg = encode_for_cli(input_value);

    % Locate CLI script relative to this file
    m_path = fileparts(mfilename('fullpath'));
    cli_main_path = fullfile(m_path, '..', 'cli', 'main.py');

    % Build system command to execute CLI roundtrip
    cmd = sprintf('%s "%s" %s --raw', python_cmd, cli_main_path, cli_arg);

    [status, cmdout] = system(cmd);
    if status ~= 0
        error('fpga_interface:matlab_interface:ExecutionError', ...
              'CLI execution failed with status %d:\n%s', status, cmdout);
    end

    % 2. Decode CLI output back into MATLAB numeric representation
    result = decode_from_cli(cmdout);
end
