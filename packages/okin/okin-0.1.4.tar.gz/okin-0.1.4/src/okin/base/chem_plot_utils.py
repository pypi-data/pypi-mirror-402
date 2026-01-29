import matplotlib.pyplot as plt

# def apply_acs_layout():
#     style = 'seaborn-v0_8-whitegrid'
#     with plt.style.context(style):
#         plt.axhline(y=0, color='k')
#         plt.axvline(x=0, color='k')
#         plt.grid(True, linestyle='--')
#         plt.xticks(weight = 'bold')
#         plt.yticks(weight = 'bold')

#         # keep all things in the image
#         # plt.tight_layout()
#         plt.subplots_adjust(top=0.85, bottom=0.15, left=0.1)
#         fig = plt.gcf()
#         # golden_ratio = 1.618
#         width = 8
#         # height = width / golden_ratio
#         height = 5
#         fig.set_size_inches(width, height)
#         # fig.set_figwidth(8)
#         # fig.set_figheight(6)
#         fig.set_dpi(100)


def apply_acs_layout_ax(ax):
    style = 'seaborn-v0_8-whitegrid'
    
    # Apply the style context (this works globally, but it's okay to use here for general styling)
    with plt.style.context(style):
        # Set horizontal and vertical lines at y=0 and x=0 respectively
        ax.axhline(y=0, color='k')
        ax.axvline(x=0, color='k')

        # Set grid lines and customize them
        ax.grid(True, linestyle='--')

        # Set tick properties (make them bold)
        ax.tick_params(axis='x', labelsize=10)  # You can set the label size here
        ax.tick_params(axis='y', labelsize=10)  # You can set the label size here

        # Alternatively, for bold ticks, set font weight directly on labels:
        for label in ax.get_xticklabels():
            label.set_fontweight('bold')
        for label in ax.get_yticklabels():
            label.set_fontweight('bold')

        # Set figure size and DPI via the figure containing the ax
        # fig = ax.figure
        # fig.set_size_inches(9, 4)  # Specify width and height in inches
        # fig.set_dpi(100)  # Set resolution (dots per inch)

        # Adjust subplot layout (this will modify the space around the plot)
        # plt.subplots_adjust(top=0.75, bottom=0.15, left=0.05, right=0.1)

        # Tight layout to avoid overlapping elements
        # fig.tight_layout()





def apply_acs_layout(): # dont ask.
    style = 'seaborn-v0_8-whitegrid'
    with plt.style.context(style):
        plt.axhline(y=0, color='k')
        plt.axvline(x=0, color='k')
        plt.grid(True, linestyle='--')
        plt.xticks(weight = 'bold')
        plt.yticks(weight = 'bold')

        # keep all things in the image
        
        plt.subplots_adjust(top=0.75, bottom=0.15, left=0.05, right=0.1)
        plt.tight_layout()
        fig = plt.gcf()
        # golden_ratio = 1.618
        # width = 6
        # height = width / golden_ratio

        width = 9
        height = 4
        # height = 5
        fig.set_size_inches(width, height)
        fig.set_dpi(100)

