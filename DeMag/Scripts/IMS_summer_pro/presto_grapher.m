

p = 2;
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

[X, Y] = meshgrid(freq-3e8, linspace(sweep_cent_freq+span/2, sweep_cent_freq-span/2, length(mag(1,:,1))));
Z = flip(permute(10*log10(mag(p,:,:).^2./50*1000), [2 3 1]));
%Z = permute(pha(p,:,:), [2 3 1]);
size(X)
size(Y)

size(Z)

surf(X, Y, Z)
colorbar;
colormap('jet')

