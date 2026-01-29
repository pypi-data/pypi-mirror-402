import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
except ImportError:
    plt = None
    sns = None
from datetime import datetime, timedelta
import json
import os

class AdvancedAnalyticsEngine:
    """
    Motor de analytics avanzado para Ailoos.
    Proporciona reportes automatizados, análisis predictivo con ML,
    tendencias de crecimiento y benchmarking contra estándares de la industria.
    """

    def __init__(self, data_source_path: str = None):
        """
        Inicializa el motor de analytics.

        Args:
            data_source_path: Ruta al archivo de datos (opcional, por defecto usa datos simulados)
        """
        self.data_source_path = data_source_path or "src/ailoos/monitoring/data/metrics_data.csv"
        self.model_failure = None
        self.model_growth = None
        self.industry_benchmarks = {
            'uptime': 99.9,  # %
            'response_time': 200,  # ms
            'error_rate': 0.1,  # %
            'throughput': 1000,  # requests/min
        }

    def _load_data(self) -> pd.DataFrame:
        """
        Carga datos de métricas. Si no existe el archivo, genera datos simulados.

        Returns:
            DataFrame con datos de métricas
        """
        if os.path.exists(self.data_source_path):
            return pd.read_csv(self.data_source_path, parse_dates=['timestamp'])
        else:
            # Generar datos simulados para demostración
            dates = pd.date_range(start='2023-01-01', end=datetime.now(), freq='H')
            np.random.seed(42)
            data = {
                'timestamp': dates,
                'uptime': np.random.normal(99.8, 0.5, len(dates)),
                'response_time': np.random.normal(150, 50, len(dates)),
                'error_rate': np.random.exponential(0.05, len(dates)),
                'throughput': np.random.normal(800, 200, len(dates)),
                'cpu_usage': np.random.normal(60, 15, len(dates)),
                'memory_usage': np.random.normal(70, 10, len(dates)),
                'failure_indicator': np.random.choice([0, 1], len(dates), p=[0.95, 0.05]),
                'user_growth': np.cumsum(np.random.normal(10, 5, len(dates))),
            }
            df = pd.DataFrame(data)
            df.to_csv(self.data_source_path, index=False)
            return df

    def generate_daily_report(self, date: str = None) -> dict:
        """
        Genera un reporte diario de métricas.

        Args:
            date: Fecha en formato YYYY-MM-DD (opcional, por defecto hoy)

        Returns:
            Diccionario con el reporte diario
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        data = self._load_data()
        daily_data = data[data['timestamp'].dt.date == pd.to_datetime(date).date()]

        if daily_data.empty:
            return {"error": f"No data available for date {date}"}

        report = {
            'date': date,
            'summary': {
                'avg_uptime': round(daily_data['uptime'].mean(), 2),
                'avg_response_time': round(daily_data['response_time'].mean(), 2),
                'total_errors': int(daily_data['error_rate'].sum()),
                'avg_throughput': round(daily_data['throughput'].mean(), 2),
                'peak_cpu': round(daily_data['cpu_usage'].max(), 2),
                'peak_memory': round(daily_data['memory_usage'].max(), 2),
            },
            'charts': self._generate_charts(daily_data, f'daily_report_{date}'),
        }

        # Guardar reporte como JSON
        report_path = f"src/ailoos/monitoring/reports/daily_report_{date}.json"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        return report

    def generate_weekly_report(self, week_start: str = None) -> dict:
        """
        Genera un reporte semanal de métricas.

        Args:
            week_start: Fecha de inicio de semana en formato YYYY-MM-DD (opcional, por defecto lunes pasado)

        Returns:
            Diccionario con el reporte semanal
        """
        if week_start is None:
            today = datetime.now()
            week_start = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')

        start_date = pd.to_datetime(week_start)
        end_date = start_date + timedelta(days=6)

        data = self._load_data()
        weekly_data = data[(data['timestamp'] >= start_date) & (data['timestamp'] <= end_date)]

        if weekly_data.empty:
            return {"error": f"No data available for week starting {week_start}"}

        report = {
            'week_start': week_start,
            'week_end': end_date.strftime('%Y-%m-%d'),
            'summary': {
                'avg_uptime': round(weekly_data['uptime'].mean(), 2),
                'avg_response_time': round(weekly_data['response_time'].mean(), 2),
                'total_errors': int(weekly_data['error_rate'].sum()),
                'avg_throughput': round(weekly_data['throughput'].mean(), 2),
                'trend_analysis': self._analyze_trends(weekly_data),
            },
            'charts': self._generate_charts(weekly_data, f'weekly_report_{week_start}'),
        }

        # Guardar reporte como JSON
        report_path = f"src/ailoos/monitoring/reports/weekly_report_{week_start}.json"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        return report

    def predict_failures(self, prediction_days: int = 7) -> dict:
        """
        Predice posibles fallos usando machine learning.

        Args:
            prediction_days: Número de días para predecir

        Returns:
            Diccionario con predicciones de fallos
        """
        data = self._load_data()

        # Preparar datos para el modelo
        features = ['uptime', 'response_time', 'error_rate', 'throughput', 'cpu_usage', 'memory_usage']
        X = data[features]
        y = data['failure_indicator']

        # Entrenar modelo si no existe
        if self.model_failure is None:
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            self.model_failure = RandomForestClassifier(n_estimators=100, random_state=42)
            self.model_failure.fit(X_train, y_train)

            # Evaluar modelo
            y_pred = self.model_failure.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)

        # Generar predicciones para los próximos días
        last_data = data[features].tail(1)
        predictions = []

        for i in range(prediction_days):
            pred_proba = self.model_failure.predict_proba(last_data)[0][1]  # Probabilidad de fallo
            predictions.append({
                'date': (datetime.now() + timedelta(days=i+1)).strftime('%Y-%m-%d'),
                'failure_probability': round(pred_proba * 100, 2),
                'risk_level': 'High' if pred_proba > 0.7 else 'Medium' if pred_proba > 0.3 else 'Low'
            })

        return {
            'model_accuracy': round(accuracy * 100, 2) if 'accuracy' in locals() else 'Model trained',
            'predictions': predictions,
            'recommendations': self._generate_recommendations(predictions)
        }

    def analyze_growth_trends(self) -> dict:
        """
        Analiza tendencias de crecimiento usando regresión lineal.

        Returns:
            Diccionario con análisis de tendencias
        """
        data = self._load_data()

        # Preparar datos para análisis de crecimiento
        data['days'] = (data['timestamp'] - data['timestamp'].min()).dt.days
        X = data[['days']]
        y = data['user_growth']

        # Entrenar modelo de regresión
        if self.model_growth is None:
            self.model_growth = LinearRegression()
            self.model_growth.fit(X, y)

        # Predicciones
        future_days = np.array([[data['days'].max() + i] for i in range(1, 31)])  # Próximos 30 días
        future_growth = self.model_growth.predict(future_days)

        # Análisis de tendencias
        slope = self.model_growth.coef_[0]
        r_squared = self.model_growth.score(X, y)

        trend = 'Growing' if slope > 0 else 'Declining'
        growth_rate = slope * 30  # Crecimiento mensual estimado

        return {
            'current_trend': trend,
            'growth_rate_daily': round(slope, 2),
            'growth_rate_monthly': round(growth_rate, 2),
            'r_squared': round(r_squared, 4),
            'future_predictions': [
                {'day': i+1, 'predicted_growth': round(future_growth[i], 2)}
                for i in range(len(future_growth))
            ],
            'chart_path': self._plot_growth_trend(data, future_growth)
        }

    def benchmark_against_industry(self) -> dict:
        """
        Compara métricas contra estándares de la industria.

        Returns:
            Diccionario con benchmarking
        """
        data = self._load_data()
        latest_data = data.tail(24)  # Últimas 24 horas

        current_metrics = {
            'uptime': latest_data['uptime'].mean(),
            'response_time': latest_data['response_time'].mean(),
            'error_rate': latest_data['error_rate'].mean(),
            'throughput': latest_data['throughput'].mean(),
        }

        benchmark_results = {}
        for metric, industry_std in self.industry_benchmarks.items():
            current = current_metrics.get(metric, 0)
            if metric in ['uptime', 'throughput']:
                performance = 'Above' if current >= industry_std else 'Below'
            else:  # response_time, error_rate
                performance = 'Below' if current <= industry_std else 'Above'

            benchmark_results[metric] = {
                'current': round(current, 2),
                'industry_standard': industry_std,
                'performance': performance,
                'gap': round(abs(current - industry_std), 2)
            }

        return {
            'benchmark_results': benchmark_results,
            'overall_score': self._calculate_overall_score(benchmark_results),
            'recommendations': self._generate_benchmark_recommendations(benchmark_results)
        }

    def _generate_charts(self, data: pd.DataFrame, filename_prefix: str) -> dict:
        """
        Genera gráficos para reportes.

        Args:
            data: DataFrame con datos
            filename_prefix: Prefijo para nombres de archivos

        Returns:
            Diccionario con rutas a gráficos generados
        """
        if plt is None:
            return {}

        charts_dir = "src/ailoos/monitoring/charts"
        os.makedirs(charts_dir, exist_ok=True)

        charts = {}

        # Gráfico de uptime
        plt.figure(figsize=(10, 6))
        plt.plot(data['timestamp'], data['uptime'])
        plt.title('Uptime Over Time')
        plt.xlabel('Time')
        plt.ylabel('Uptime (%)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        uptime_path = f"{charts_dir}/{filename_prefix}_uptime.png"
        plt.savefig(uptime_path)
        plt.close()
        charts['uptime_chart'] = uptime_path

        # Gráfico de response time
        plt.figure(figsize=(10, 6))
        plt.plot(data['timestamp'], data['response_time'])
        plt.title('Response Time Over Time')
        plt.xlabel('Time')
        plt.ylabel('Response Time (ms)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        response_path = f"{charts_dir}/{filename_prefix}_response_time.png"
        plt.savefig(response_path)
        plt.close()
        charts['response_time_chart'] = response_path

        return charts

    def _analyze_trends(self, data: pd.DataFrame) -> dict:
        """
        Analiza tendencias en datos semanales.

        Args:
            data: DataFrame con datos semanales

        Returns:
            Diccionario con análisis de tendencias
        """
        trends = {}
        for column in ['uptime', 'response_time', 'error_rate', 'throughput']:
            start_value = data[column].iloc[0]
            end_value = data[column].iloc[-1]
            trend = 'Improving' if (column in ['uptime', 'throughput'] and end_value > start_value) or \
                    (column in ['response_time', 'error_rate'] and end_value < start_value) else 'Declining'
            change_percent = ((end_value - start_value) / start_value) * 100 if start_value != 0 else 0
            trends[column] = {
                'trend': trend,
                'change_percent': round(change_percent, 2),
                'start_value': round(start_value, 2),
                'end_value': round(end_value, 2)
            }
        return trends

    def _generate_recommendations(self, predictions: list) -> list:
        """
        Genera recomendaciones basadas en predicciones de fallos.

        Args:
            predictions: Lista de predicciones

        Returns:
            Lista de recomendaciones
        """
        high_risk_days = [p for p in predictions if p['risk_level'] == 'High']
        recommendations = []

        if high_risk_days:
            recommendations.append("Alto riesgo de fallos detectado. Recomendaciones:")
            recommendations.append("- Realizar mantenimiento preventivo")
            recommendations.append("- Aumentar capacidad de recursos")
            recommendations.append("- Implementar failover automático")

        return recommendations

    def _plot_growth_trend(self, data: pd.DataFrame, future_growth: np.ndarray) -> str:
        """
        Genera gráfico de tendencia de crecimiento.

        Args:
            data: DataFrame con datos históricos
            future_growth: Predicciones futuras

        Returns:
            Ruta al archivo del gráfico
        """
        if plt is None:
            return ""

        charts_dir = "src/ailoos/monitoring/charts"
        os.makedirs(charts_dir, exist_ok=True)

        plt.figure(figsize=(12, 8))
        plt.plot(data['timestamp'], data['user_growth'], label='Historical Growth')
        future_dates = [data['timestamp'].max() + timedelta(days=i+1) for i in range(len(future_growth))]
        plt.plot(future_dates, future_growth, label='Predicted Growth', linestyle='--')
        plt.title('User Growth Trend Analysis')
        plt.xlabel('Date')
        plt.ylabel('User Growth')
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        chart_path = f"{charts_dir}/growth_trend_analysis.png"
        plt.savefig(chart_path)
        plt.close()

        return chart_path

    def _calculate_overall_score(self, benchmark_results: dict) -> float:
        """
        Calcula puntuación general de benchmarking.

        Args:
            benchmark_results: Resultados del benchmarking

        Returns:
            Puntuación general (0-100)
        """
        scores = []
        for metric, result in benchmark_results.items():
            if result['performance'] == 'Above':
                score = 100
            elif result['performance'] == 'Below':
                # Penalización basada en la brecha
                gap_ratio = result['gap'] / result['industry_standard']
                score = max(0, 100 - (gap_ratio * 50))
            else:
                score = 50  # Neutral
            scores.append(score)

        return round(np.mean(scores), 2)

    def _generate_benchmark_recommendations(self, benchmark_results: dict) -> list:
        """
        Genera recomendaciones basadas en benchmarking.

        Args:
            benchmark_results: Resultados del benchmarking

        Returns:
            Lista de recomendaciones
        """
        recommendations = []
        for metric, result in benchmark_results.items():
            if result['performance'] == 'Below':
                if metric == 'uptime':
                    recommendations.append("Mejorar uptime mediante redundancia y monitoreo continuo")
                elif metric == 'response_time':
                    recommendations.append("Optimizar response time con caching y mejora de infraestructura")
                elif metric == 'error_rate':
                    recommendations.append("Reducir error rate mediante mejor manejo de excepciones y testing")
                elif metric == 'throughput':
                    recommendations.append("Aumentar throughput con escalado horizontal")

        return recommendations