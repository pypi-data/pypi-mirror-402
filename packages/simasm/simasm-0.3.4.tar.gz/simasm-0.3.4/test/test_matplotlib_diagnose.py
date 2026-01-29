"""
Diagnostic script to identify matplotlib display issues.
"""
import sys
import matplotlib
print(f"Python version: {sys.version}")
print(f"Matplotlib version: {matplotlib.__version__}")
print(f"Matplotlib backend: {matplotlib.get_backend()}")
print(f"Platform: {sys.platform}")

# Test 1: Check if Tk is available
print("\n=== Test 1: Tk availability ===")
try:
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    print("[OK] Tkinter is available")
    root.destroy()
except Exception as e:
    print(f"[FAIL] Tkinter not available: {e}")

# Test 2: Check backend capabilities
print("\n=== Test 2: Backend capabilities ===")
print(f"Interactive: {matplotlib.is_interactive()}")
try:
    import matplotlib.pyplot as plt
    print(f"Backend after pyplot import: {matplotlib.get_backend()}")
    print(f"GUI backends available: {matplotlib.rcsetup.interactive_bk}")
except Exception as e:
    print(f"Error: {e}")

# Test 3: Try to create and show a simple plot
print("\n=== Test 3: Simple plot test ===")
try:
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot([1, 2, 3], [1, 4, 2])
    ax.set_title("Test Plot")

    print(f"Figure created: {fig}")
    print(f"Figure has canvas: {hasattr(fig, 'canvas')}")
    print(f"Canvas type: {type(fig.canvas)}")

    if hasattr(fig.canvas, 'manager'):
        print(f"Has manager: True")
        print(f"Manager type: {type(fig.canvas.manager)}")

        if hasattr(fig.canvas.manager, 'window'):
            print(f"Has window: True")
            print(f"Window type: {type(fig.canvas.manager.window)}")
        else:
            print(f"Has window: False")
    else:
        print(f"Has manager: False")

    print("\nAttempting to show figure...")
    print("(This should display a window. Close it to continue.)")

    # Try showing with fig.show()
    try:
        fig.show()
        plt.pause(0.1)
        print("[OK] fig.show() succeeded")
    except Exception as e:
        print(f"[FAIL] fig.show() failed: {e}")

    # Try showing with plt.show(block=True)
    try:
        print("\nCalling plt.show(block=True)...")
        plt.show(block=True)
        print("[OK] plt.show() completed")
    except Exception as e:
        print(f"[FAIL] plt.show() failed: {e}")

    plt.close(fig)

except Exception as e:
    print(f"[FAIL] Test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Diagnostic complete ===")
