function fpgaPacket = prepareFPGAInput(matlabResult)
% PREPAREFPGAINPUT Converts Solar Gimbal MATLAB result into deterministic FPGA hardware packet.
%
% Architecture Role:
%   Centralizes the binary / register format for transfer to the Zynq-7000 FPGA
%   processing system (PS) over UART/Ethernet, which then feeds AXI registers
%   in the programmable logic (PL).
%
% Syntax:
%   fpgaPacket = prepareFPGAInput(matlabResult)
%
% Outputs:
%   fpgaPacket - struct containing:
%                  .scene_id         (uint8, 2 = Solar Gimbal)
%                  .sun_azimuth      (single)
%                  .sun_elevation    (single)
%                  .panel_azimuth    (single)
%                  .panel_elevation  (single)
%                  .azimuth_error    (single)
%                  .elevation_error  (single)
%                  .status_byte      (uint8)
%                  .checksum         (uint16)

    if nargin < 1 || isempty(matlabResult)
        error('prepareFPGAInput:EmptyInput', 'matlabResult struct cannot be empty.');
    end

    sceneID = uint8(2); % Scene ID 2 represents Solar Gimbal

    sAz = single(matlabResult.sunAzimuth);
    sEl = single(matlabResult.sunElevation);
    pAz = single(matlabResult.panelAzimuth);
    pEl = single(matlabResult.panelElevation);
    azErr = single(matlabResult.azimuthError);
    elErr = single(matlabResult.elevationError);

    statusByte = uint8(7); % 0x07 = ACTIVE_VALID_TRACKING

    % 16-bit additive packet verification checksum
    chk = uint16(sceneID) + ...
          uint16(mod(typecast(sAz, 'uint32'), 65535)) + ...
          uint16(mod(typecast(sEl, 'uint32'), 65535)) + ...
          uint16(mod(typecast(pAz, 'uint32'), 65535)) + ...
          uint16(mod(typecast(pEl, 'uint32'), 65535)) + ...
          uint16(mod(typecast(azErr, 'uint32'), 65535)) + ...
          uint16(mod(typecast(elErr, 'uint32'), 65535));

    fpgaPacket = struct( ...
        'scene_id', sceneID, ...
        'sun_azimuth', sAz, ...
        'sun_elevation', sEl, ...
        'panel_azimuth', pAz, ...
        'panel_elevation', pEl, ...
        'azimuth_error', azErr, ...
        'elevation_error', elErr, ...
        'status_byte', statusByte, ...
        'checksum', chk);
end
