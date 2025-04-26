import os

def process_waypoint_file(filename):
    # Read the waypoint file
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    # Process each line
    new_lines = []
    for line in lines:
        if line.strip() == 'QGC WPL 110' or not line.strip():
            new_lines.append(line)
            continue
            
        parts = line.strip().split('\t')
        if len(parts) >= 10:
            try:
                # Get the longitude value (10th column, index 9)
                lon = float(parts[8])
                # Add 0.0003 to longitude
                new_lon = lon - 0.00011
                # Replace the old longitude with new value
                parts[8] = f'{new_lon:.8f}'
                # Join back together with tabs
                new_line = '\t'.join(parts) + '\n'
                new_lines.append(new_line)
            except ValueError:
                # If conversion fails, keep original line
                new_lines.append(line)
        else:
            new_lines.append(line)
    
    # Write back to a new file
    output_filename = os.path.splitext(filename)[0] + '_processed02.waypoints'
    with open(output_filename, 'w') as f:
        f.writelines(new_lines)
    
    return output_filename

if __name__ == '__main__':
    input_file = '20250210.waypoints'
    processed_file = process_waypoint_file(input_file)
    print(f'Processed file saved as: {processed_file}')
