import React from "react";
import { Range, getTrackBackground } from "react-range";

const SemiCircleSlider = ({ value, onChange, locked }) => {
  const STEP = 0.01;
  const MIN = 0;
  const MAX = 1;

  const values = React.useMemo(() => [value], [value]);

  const handleChange = (newValues) => {
    if (!locked) {
      onChange(newValues[0]);
    }
  };

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        flexWrap: "wrap"
      }}
    >
      <Range
        values={values}
        step={STEP}
        min={MIN}
        max={MAX}
        onChange={handleChange}
        renderTrack={({ props, children }) => (
          <div
            onMouseDown={props.onMouseDown}
            onTouchStart={props.onTouchStart}
            style={{
              ...props.style,
              height: "36px",
              display: "flex",
              width: "100%"
            }}
          >
            <div
              ref={props.ref}
              style={{
                height: "5px",
                width: "100%",
                borderRadius: "4px",
                background: getTrackBackground({
                  values,
                  colors: ["#ccc", "#548BF4", "#ccc"],
                  min: MIN,
                  max: MAX
                }),
                alignSelf: "center"
              }}
            >
              {children}
            </div>
          </div>
        )}
        renderThumb={({ props }) => (
          <div
            {...props}
            style={{
              ...props.style,
              height: "16px",
              width: "16px",
              borderRadius: "50%",
              backgroundColor: "#FFF",
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              boxShadow: "0px 2px 6px #AAA"
            }}
          >
            <div
              style={{
                height: "8px",
                width: "8px",
                borderRadius: "50%",
                backgroundColor: "#548BF4"
              }}
            />
          </div>
        )}
      />
    </div>
  );
};

export default SemiCircleSlider;
