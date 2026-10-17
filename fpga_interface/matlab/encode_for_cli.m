function cli_input_str = encode_for_cli(numeric_val)
% ENCODE_FOR_CLI Format MATLAB numerical value for the fpga_interface CLI interface.
%
% Responsibilities:
%   - Convert MATLAB numerical data into the deterministic representation required by the CLI protocol.
%   - Keep MATLAB-to-CLI conversion deterministic.
%   - Do NOT create an independent incompatible binary encoding scheme.
%   - The authoritative binary encoding definition remains in Python/protocol.json.
%
% Inputs:
%   numeric_val - MATLAB numeric scalar (e.g., 25)
%
% Outputs:
%   cli_input_str - Human-readable integer string suitable for CLI input (e.g., '25')

    if ~isnumeric(numeric_val) || ~isscalar(numeric_val)
        error('fpga_interface:encode_for_cli:InvalidInput', ...
              'Input must be a numeric scalar value.');
    end

    % Check if input has fractional part
    if floor(numeric_val) ~= numeric_val
        error('fpga_interface:encode_for_cli:NonIntegerValue', ...
              'Value must be an integer.');
    end

    % Format as deterministic integer string representation
    cli_input_str = sprintf('%d', fix(numeric_val));
end
