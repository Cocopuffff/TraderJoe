import React, { useEffect, useState, useContext } from "react";
import ErrorContext from "../context/ErrorContext";
import styles from "./Chart.module.css";
import Spinner from "./Spinner";
import ReactECharts from "echarts-for-react";
import * as echarts from "echarts/core";
import { CandlestickChart } from "echarts/charts";
import {
  GridComponent,
  ToolboxComponent,
  TooltipComponent,
  TitleComponent,
  DatasetComponent,
} from "echarts/components";
import {
  // CanvasRenderer,
  SVGRenderer,
} from "echarts/renderers";

echarts.use([
  TitleComponent,
  TooltipComponent,
  ToolboxComponent,
  GridComponent,
  CandlestickChart,
  DatasetComponent,
  SVGRenderer,
]);

const downColour = "#E1484C";
const upColour = "#429782";

const Chart = (props) => {
  // const [data, setData] = useState(null);
  const [values, setValues] = useState([]);
  const [volumes, setVolume] = useState([]);
  const [dateTimes, setDateTimes] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const ErrorCtx = useContext(ErrorContext);

  const options = {
    grid: [
      {
        left: "5%",
        right: "0%",
        height: "70%",
      },
      {
        left: "5%",
        right: "0%",
        top: "80%",
        height: "15%",
      },
    ],
    xAxis: [
      {
        type: "category",
        data: dateTimes,
        boundaryGap: true,
        axisLine: { onZero: false },
        splitLine: { show: false },
        axisLabel: {
          formatter: function (value) {
            return `${value.substring(8, 10)}/${value.substring(
              5,
              7
            )}/${value.substring(0, 4)}`;
          },
        },
        min: "dataMin",
        max: "dataMax",
        axisPointer: {
          z: 100,
        },
      },
      {
        type: "category",
        gridIndex: 1,
        data: dateTimes,
        boundaryGap: true,
        axisLine: { onZero: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        min: "dataMin",
        max: "dataMax",
      },
    ],
    yAxis: [
      {
        scale: true,
        splitArea: {
          show: true,
        },
      },
      {
        scale: true,
        gridIndex: 1,
        splitNumber: 2,
        axisLabel: { show: false },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
      },
    ],
    dataZoom: [
      {
        type: "inside",
        xAxisIndex: [0, 1],
        start: 60,
        end: 100,
      },
    ],
    series: [
      {
        name:
          props.selectedInstrument &&
          props.selectedInstrument.fields.displayName,
        data: values,
        type: "candlestick",
        itemStyle: {
          color: upColour,
          color0: downColour,
          borderColor: undefined,
          borderColor0: undefined,
        },
      },
      {
        name: "Volume",
        type: "bar",
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volumes,
        itemStyle: {
          color: function (parameter) {
            return parameter.data[2] > 0 ? upColour : downColour;
          },
        },
      },
    ],
    tooltip: {
      trigger: "axis",
      axisPointer: {
        type: "cross",
      },
      padding: 10,
      position: function (pos, params, el, elRect, size) {
        const obj = {
          top: 0,
        };
        obj[["left", "right"][+(pos[0] < size.viewSize[0] / 2)]] = 100;
        return obj;
      },
    },
    axisPointer: {
      link: [
        {
          xAxisIndex: "all",
        },
      ],
      label: {
        backgroundColor: "#4e4e4e",
      },
    },
    toolbox: {
      feature: {
        dataZoom: {
          yAxisIndex: false,
        },
        brush: {
          type: ["lineX", "clear"],
        },
      },
    },
    brush: {
      xAxisIndex: "all",
      brushLink: "all",
      outOfBrush: {
        colorAlpha: 0.1,
      },
    },
    visualMap: {
      show: false,
      seriesIndex: 5,
      dimension: 2,
      pieces: [
        {
          value: 1,
          color: downColour,
        },
        {
          value: -1,
          color: upColour,
        },
      ],
    },
    title: {
      text:
        props.selectedInstrument && props.selectedInstrument.fields.displayName,
      left: "center",
      top: "top",
      textStyle: {
        color: "#fff",
        fontSize: 20,
        fontWeight: "normal",
      },
    },
  };

  const processData = (rawData) => {
    let categoryData = [];
    let values = [];
    let volumes = [];

    for (let i = 0; i < rawData.candles.length; i++) {
      let value = [
        rawData.candles[i].mid.o,
        rawData.candles[i].mid.c,
        rawData.candles[i].mid.l,
        rawData.candles[i].mid.h,
      ];
      categoryData.push(rawData.candles[i].time);
      values.push(value);
      volumes.push([
        i,
        rawData.candles[i].volume,
        rawData.candles[i].mid.c >= rawData.candles[i].mid.o ? 1 : -1,
      ]);
    }
    return {
      categoryData: categoryData,
      values: values,
      volumes: volumes,
    };
  };

  const updateLatestCandles = (RawData, latestCandlesData) => {
    const CandlesData = structuredClone(RawData);
    for (const candle of latestCandlesData) {
      let isInCandlesData = false;
      for (let i = CandlesData.candles.length - 1; i >= 0; i--) {
        if (JSON.stringify(candle) === JSON.stringify(CandlesData.candles[i])) {
          isInCandlesData = true;
        }
      }
      if (!isInCandlesData) {
        CandlesData.candles.push(candle);
      }
    }
    return CandlesData;
  };

  const getData = async (signal) => {
    try {
      if (!props.selectedInstrument) {
        return;
      }
      setIsLoading(true);
      let url1 = `${import.meta.env.VITE_FXPRACTICE_OANDA}/v3/instruments/${
        props.selectedInstrument.fields.name
      }/candles`;

      if (props.granularity || props.count || props.from || props.to) {
        url1 = url1.concat("?");
      }

      props.granularity
        ? (url1 = url1.concat(`&granularity=${props.granularity}`))
        : "";
      props.count ? (url1 = url1.concat(`&count=${props.count}`)) : "";
      props.from ? (url1 = url1.concat(`&from=${props.from}`)) : "";
      props.to ? (url1 = url1.concat(`&to=${props.to}`)) : "";

      let url2 = `${import.meta.env.VITE_FXPRACTICE_OANDA}/v3/accounts/${
        import.meta.env.VITE_OANDA_ACCOUNT
      }/candles/latest?candleSpecifications=${
        props.selectedInstrument.fields.name
      }:${props.granularity}:M`;

      const res1 = await fetch(url1, {
        signal,
        headers: {
          Authorization: "Bearer " + import.meta.env.VITE_OANDA_DEMO_API_KEY,
          Connection: "Keep-Alive",
        },
      });

      const res2 = await fetch(url2, {
        signal,
        headers: {
          Authorization: "Bearer " + import.meta.env.VITE_OANDA_DEMO_API_KEY,
          Connection: "Keep-Alive",
        },
      });

      if (res1.ok && res2.ok) {
        const data1 = await res1.json();
        const data2 = await res2.json();
        const latestCandles = data2.latestCandles[0].candles;
        const updatedData = updateLatestCandles(data1, latestCandles);
        const processedData = processData(updatedData);

        setValues(processedData.values);
        setVolume(processedData.volumes);
        setDateTimes(processedData.categoryData);
        setIsLoading(false);
      }
    } catch (error) {
      if (error.name !== "AbortError") {
        console.log(error.message);
        ErrorCtx.setIsError(true);
        ErrorCtx.setErrorMessage(error.message);
      }
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const controller = new AbortController();
    getData(controller.signal);

    return () => {
      controller.abort();
    };
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    getData(controller.signal);
    return () => {
      controller.abort();
    };
  }, [
    props.selectedInstrument,
    props.granularity,
    props.count,
    props.from,
    props.to,
  ]);

  return (
    <div className={`container-fluid py-3 ${styles.chartContainer}`}>
      {isLoading ? (
        <Spinner />
      ) : (
        <ReactECharts
          option={options}
          style={{ height: "100%", width: "100%", overflowY: "scroll" }}
        />
      )}
    </div>
  );
};

export default Chart;
