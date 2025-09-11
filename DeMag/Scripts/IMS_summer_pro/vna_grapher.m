
for i = 1:7
    plot(linspace(vna_parameters(1,1), vna_parameters(1,2), 1001), permute(vna_data(i,1,:), [1 3 2]))
    hold on
end