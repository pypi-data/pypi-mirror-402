"""
Quick test to check matplotlib backend and plot display.
"""
import matplotlib
print(f"Backend before pyplot import: {matplotlib.get_backend()}")

import matplotlib.pyplot as plt
print(f"Backend after pyplot import: {matplotlib.get_backend()}")

# Create a simple test plot
fig, ax = plt.subplots()
ax.plot([1, 2, 3, 4], [1, 4, 2, 3])
ax.set_title("Test Plot")

print(f"Figure created. Showing with block=True...")
plt.show(block=True)
print("Plot closed.")
