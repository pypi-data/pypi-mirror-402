import math
import matplotlib.pyplot as plt
from .Generaldistribution import Distribution

class Binomial(Distribution):
    """ Binomial distribution class for calculating and 
    visualizing a Binomial distribution.
    
    Attributes:
        mean (float) representing the mean value of the distribution
        stdev (float) representing the standard deviation of the distribution
        data_list (list of floats) a list of floats to be extracted from the data file
        p (float) representing the probability of an event occurring
                
    """
        
    def __init__(self, p, n):
        """ Initialize Binomial object, inheriting from the Distribution class
        assign p and n based on input, and calculate the mean and stdev, calling on class methods
        
        Args: 
            p, probability of distribution
            n, number of samples
        
        Returns: 
            None
        """
        
        Distribution.__init__(self)
        self.p = p
        self.n = n
        
        self.calculate_mean()
        self.calculate_stdev()

    def calculate_mean(self):
        """Function to calculate the mean from p and n
        
        Args: 
            None
        
        Returns: 
            float: mean of the data set
    
        """
        avg = self.p * self.n
        
        self.mean = avg

        return self.mean

    def calculate_stdev(self):
        """Function to calculate the standard deviation from p and n.
        
        Args: 
            None
        
        Returns: 
            float: standard deviation of the data set
    
        """
        sigma = math.sqrt(self.n * self.p * (1 - self.p))
        
        self.stdev = sigma
            
        return self.stdev

    def replace_stats_with_data(self):
        """Function to calculate p and n from the data set. The function updates the p and n variables of the object.
        
        Args: 
            None
        
        Returns: 
            float: the p value
            float: the n value
    
        """
        
        data_list = self.data
        if data_list:

            num_trials = len(data_list)       
            pos_trials = sum(data_list)

            self.n = num_trials
            self.p = pos_trials / num_trials

            self.calculate_mean()
            self.calculate_stdev()
        else:
            print("Error: Data list is empty.")
            return None

        return self.p, self.n
    
    def plot_bar(self):
        """Function to output a histogram of the instance variable data using 
        matplotlib pyplot library.
        
        Args:
            None
            
        Returns:
            None
        """
        labels = ['0', '1']
        counts = [self.data.count(0), self.data.count(1)]
        
        plt.bar(labels, counts)

        plt.title('Bar plot of data outcomes')
        plt.xlabel('Outcomes')
        plt.ylabel('Count')

        plt.show()
    
    def pdf(self, k):
        """Probability density function calculator for the binomial distribution.
        
        Args:
            k (float): point for calculating the probability density function
            
        
        Returns:
            float: probability density function output
        """
        if self.n >= k and k >= 0:
            binom_coeff = math.factorial(int(self.n)) / (math.factorial(int(k)) * math.factorial(int(self.n - k)))
            pdf_k = binom_coeff * ((self.p ** k) * ((1 - self.p) ** (self.n - k)))
        else:
            print('Variable k is invalid for calculation; k must be 0 < k < n')
            return 0.0

        return pdf_k
        

    def plot_pdf(self):

        """Function to plot the pdf of the binomial distribution
        
        Args:
            None
        
        Returns:
            list: x values for the pdf plot
            list: y values for the pdf plot
            
        """
    
        pdf_plot_x_list = []
        pdf_plot_y_list = []

        for i in range(self.n + 1):
            x_value = i
            y_value = self.pdf(i)
            pdf_plot_x_list.append(x_value)
            pdf_plot_y_list.append(y_value)

        plt.bar(pdf_plot_x_list, pdf_plot_y_list)

        plt.title('Bar plot of pdf function of the distribution')
        plt.xlabel('k-value')
        plt.ylabel('pdf')

        plt.show()

        return pdf_plot_x_list, pdf_plot_y_list

                
    def __add__(self, other):
        
        """Function to add together two Binomial distributions with equal p
        
        Args:
            other (Binomial): Binomial instance
            
        Returns:
            Binomial: Binomial distribution
            
        """
        
        try:
            assert self.p == other.p, 'p values are not equal'
        except AssertionError as error:
            raise

        result = Binomial(self.p, self.n + other.n)

        return result
                        
    def __repr__(self):
    
        """Function to output the characteristics of the Binomial instance
        
        Args:
            None
        
        Returns:
            string: characteristics of the Binomial object
        
        """
    
        return f'mean {self.mean}, standard deviation {self.stdev}, p {self.p}, n {self.n}'
