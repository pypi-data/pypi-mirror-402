import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def main():
    # Generate random data
    np.random.seed(42)
    df = pd.DataFrame({
        'x': np.arange(100),
        'y': np.random.randn(100).cumsum()
    })
    
    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(df['x'], df['y'], label='Random Walk')
    plt.title("Sample Data Plot")
    plt.xlabel("Step")
    plt.ylabel("Value")
    plt.legend()
    plt.grid(True)
    
    print("Plot generated successfully.")
    # plt.show() # Commented out for non-interactive execution

if __name__ == "__main__":
    main()
