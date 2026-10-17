function numeric_val = decode_from_cli(cli_output_str)
% DECODE_FROM_CLI Convert values received through the CLI back into MATLAB numerical data.
%
% Responsibilities:
%   - Convert values received through the CLI back into MATLAB numerical data.
%   - Maintain the same protocol definition used by Python and Verilog.
%
% Inputs:
%   cli_output_str - String output returned from CLI execution
%
% Outputs:
%   numeric_val - MATLAB numeric scalar

    if ~ischar(cli_output_str) && ~isstring(cli_output_str)
        error('fpga_interface:decode_from_cli:InvalidInput', ...
              'CLI output must be a string or char array.');
    end

    raw_str = strtrim(char(cli_output_str));

    % Direct numeric parse attempt
    num = str2double(raw_str);
    if ~isnan(num)
        numeric_val = num;
        return;
    end

    % If full formatted output was returned, look for patterns such as:
    % "[OUTPUT DECODED] Value: 25" or "Python Decoded Value : 25"
    tokens = regexp(raw_str, '(?:Value\s*:\s*|Decoded\s+Value\s*:\s*)(-?\d+)', 'tokens');
    if ~isempty(tokens)
        numeric_val = str2double(tokens{end}{1});
        return;
    end

    % Fallback: find any trailing integer token
    tokens_num = regexp(raw_str, '(-?\d+)\s*$', 'tokens');
    if ~isempty(tokens_num)
        numeric_val = str2double(tokens_num{1}{1});
        return;
    end

    error('fpga_interface:decode_from_cli:ParseError', ...
          'Failed to decode numerical value from CLI output: %s', raw_str);
end
